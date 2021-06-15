import random
import re
from textwrap import dedent
from bs4 import BeautifulSoup as Soup
from tqdm.notebook import tqdm

from renderapi.stack import (get_stack_bounds, get_z_values_for_stack,
                             create_stack, set_stack_state)
from renderapi.tilespec import TileSpec, Layout, get_tile_specs_from_z
from renderapi.client import import_tilespecs
from renderapi.transform import AffineModel


def get_random_ints(N):
    """Generate a random integer with cardinality N"""
    lower = 10**(N-1)
    upper = 10**N - 1
    return random.randint(lower,upper)


def create_patch_xml(tile_spec):
    """Generate xml data for a given patch (tile)"""
    # Abbreviate tile specification
    ts = tile_spec
    # Generate oid
    x, y = [int(i) for i in re.findall(r'\d+', ts.tileId)[-2:]]
    oid = f"{ts.z:.0f}{x:02d}{y:02d}"
    # Get total transform
    AT = AffineModel()
    for tform in ts.tforms:
        AT = tform.concatenate(AT)
    # Create xml data for patch
    patch = f"""
            <t2_patch
                oid="{oid}"
                width="{ts.width}"
                height="{ts.height}"
                transform="matrix({AT.M00},{AT.M10},{AT.M01},{AT.M11},{AT.B0},{AT.B1})"
                links=""
                type="1"
                file_path="{ts.ip[0].imageUrl.split('://')[1]}"
                title="{ts.tileId}"
                style="fill-opacity:1.0;stroke:#ffff00;"
                o_width="{ts.width:.0f}"
                o_height="{ts.height:.0f}"
                min="{ts.minint}"
                max="{ts.maxint}"
                mres="32"
            >
            </t2_patch>"""
    return patch


def create_layer_xml(stack, z, render):
    """Generate xml data for a given z layer"""
    # Create xml header data for layer
    layer = f"""
        <t2_layer
            oid="{z:.0f}"
            thickness="1.0"
            z="{z:.1f}"
            title="layer_{z:.0f}"
        >"""
    # Fetch tiles in layer
    tile_specs = get_tile_specs_from_z(stack=stack,
                                       z=z,
                                       render=render)
    # Loop through tiles
    for ts in tile_specs:
        # Add patch data to layer
        patch = create_patch_xml(ts)
        layer += patch
    # Add layer footer
    layer += """
        </t2_layer>"""
    return layer


def create_stack_xml(stack, z_values=None, render=None):
    """Generate xml data for a given stack"""
    # Fetch z values for stack
    if z_values is None:
        z_values = get_z_values_for_stack(stack=stack, render=render)
    # Initialize stack xml data (empty string)
    stack_data = ""
    # Loop through z layers
    for z in tqdm(z_values):
        # Add layer data to stack
        layer = create_layer_xml(stack=stack,
                                 z=z,
                                 render=render)
        stack_data += layer
    return stack_data


def create_trakem2_project(stack, xml_filepath, z_values=None, render=None):
    """Create TrakEM2 project xml file for a given stack"""
    # Get TrakEM2 header
    xml_header = create_header()
    # Create project header
    xml_project_header = create_project_header(xml_filepath)
    # Create layer set
    stack_bounds = get_stack_bounds(stack, render=render)
    width, height = (stack_bounds['maxX'] - stack_bounds['minX'],
                     stack_bounds['maxY'] - stack_bounds['minY'])
    xml_layer_set = create_layer_xml(width=width,
                                     height=height)
    # Create stack xml data
    xml_stack = create_stack_xml(stack, z_values, render)
    # Create header
    xml_footer = create_footer()
    with xml_filepath.open('w', encoding='utf-8') as xml:
        xml.write(xml_header)
        xml.write(xml_project_header)
        xml.write(xml_layer_set)
        xml.write(xml_stack)
        xml.write(xml_footer)


def import_trakem2_project(stack, xml_filepath, render):
    """Import render stack from TrakEM2 xml file"""
    # Soupify TrakEM2 xml file
    soup = Soup(xml_filepath.read_bytes(), 'lxml')

    # Iterate through layers to collect tile specifications
    tile_specs = []
    out = f"Creating tile specifications for \033[1m{stack}\033[0m..."
    print(out)
    for layer in tqdm(soup.find_all('t2_layer')):

        # Iterate through patches
        for patch in layer.find_all('t2_patch'):

            # Get patch data as dict
            d = patch.attrs

            # Parse transform data
            M00, M10, M01, M11, B0, B1 = [float(i) for i in re.findall(
                r'-?[\d.]+(?:[Ee]-?\d+)?', d['transform'])]
            A = AffineModel(M00, M01, M10, M11, B0, B1)

            # Define layout
            z = float(layer.attrs['z'])
            col, row = [int(i) for i in re.findall(r'\d+', d['title'])][-2:]
            layout = Layout(sectionId=f'S{int(z):03d}',
                            imageRow=row,
                            imageCol=col)

            # Create tile specification
            ts = TileSpec(tileId=d['title'],
                          z=z,
                          width=d['width'],
                          height=d['height'],
                          imageUrl=d['file_path'],
                          minint=d['min'],
                          maxint=d['max'],
                          layout=layout,
                          tforms=[A])
            # Collect tile specification
            tile_specs.append(ts)

    # Create stack
    create_stack(stack=stack,
                 render=render)
    # Import TileSpecs to render
    out = f"Importing tile specifications to \033[1m{stack}\033[0m..."
    print(out)
    import_tilespecs(stack=stack,
                     tilespecs=tile_specs,
                     render=render)
    # Close stack
    set_stack_state(stack=stack,
                    state='COMPLETE',
                    render=render)
    out = f"Stack \033[1m{stack}\033[0m created successfully."
    print(out)


def create_project_header(xml_filepath):
    """Generate project data for xml file"""
    # Create a long string of random numbers
    p1 = get_random_ints(13)
    p2 = get_random_ints(9)
    p3 = get_random_ints(10)
    unuid = f"{p1}.{p2}.{p3}"
    # Project header data
    project_header = f"""\
        unuid="{unuid}"
        mipmaps_folder="{xml_filepath.parent.absolute().as_posix()}/trakem2.{unuid}/trakem2.mipmaps/"
        storage_folder="{xml_filepath.parent.absolute().as_posix()}/"
        mipmaps_format="4"
        image_resizing_mode="Area downsampling"
    >
    </project>"""
    return project_header


def create_layer_set(width=7000, height=7000):
    """Generate layer set data for xml file"""
    # I think this sets up the canvas?
    layer_set = f"""
    <t2_layer_set
        oid="3"
        width="{width:.1f}"
        height="{height:.1f}"
        transform="matrix(1.0,0.0,0.0,1.0,0.0,0.0)"
        title="Top Level"
        links=""
        layer_width="{width:.1f}"
        layer_height="{height:.1f}"
        rot_x="0.0"
        rot_y="0.0"
        rot_z="0.0"
        snapshots_quality="true"
        snapshots_mode="Full"
        color_cues="true"
        area_color_cues="true"
        avoid_color_cue_colors="false"
        n_layers_color_cue="0"
        paint_arrows="true"
        paint_tags="true"
        paint_edge_confidence_boxes="true"
        prepaint="false"
        preload_ahead="0"
    >"""
    return layer_set


def create_header():
    """Boilerplate xml header data for TrakEM2 projects"""
    header = dedent("""\
    <?xml version="1.0" encoding="ISO-8859-1"?>
    <!DOCTYPE trakem2_anything [
        <!ELEMENT trakem2 (project,t2_layer_set,t2_display)>
        <!ELEMENT project (anything)>
        <!ATTLIST project id NMTOKEN #REQUIRED>
        <!ATTLIST project unuid NMTOKEN #REQUIRED>
        <!ATTLIST project title NMTOKEN #REQUIRED>
        <!ATTLIST project preprocessor NMTOKEN #REQUIRED>
        <!ATTLIST project mipmaps_folder NMTOKEN #REQUIRED>
        <!ATTLIST project storage_folder NMTOKEN #REQUIRED>
        <!ELEMENT anything EMPTY>
        <!ATTLIST anything id NMTOKEN #REQUIRED>
        <!ATTLIST anything expanded NMTOKEN #REQUIRED>
        <!ELEMENT t2_layer (t2_patch,t2_label,t2_layer_set,t2_profile)>
        <!ATTLIST t2_layer oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer thickness NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer z NMTOKEN #REQUIRED>
        <!ELEMENT t2_layer_set (t2_prop,t2_linked_prop,t2_annot,t2_layer,t2_pipe,t2_ball,t2_area_list,t2_calibration,t2_stack,t2_treeline)>
        <!ATTLIST t2_layer_set oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set transform NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set style NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set locked NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set visible NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set title NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set links NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set composite NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set layer_width NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set layer_height NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set rot_x NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set rot_y NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set rot_z NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set snapshots_quality NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set color_cues NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set area_color_cues NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set avoid_color_cue_colors NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set n_layers_color_cue NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set paint_arrows NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set paint_tags NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set paint_edge_confidence_boxes NMTOKEN #REQUIRED>
        <!ATTLIST t2_layer_set preload_ahead NMTOKEN #REQUIRED>
        <!ELEMENT t2_calibration EMPTY>
        <!ATTLIST t2_calibration pixelWidth NMTOKEN #REQUIRED>
        <!ATTLIST t2_calibration pixelHeight NMTOKEN #REQUIRED>
        <!ATTLIST t2_calibration pixelDepth NMTOKEN #REQUIRED>
        <!ATTLIST t2_calibration xOrigin NMTOKEN #REQUIRED>
        <!ATTLIST t2_calibration yOrigin NMTOKEN #REQUIRED>
        <!ATTLIST t2_calibration zOrigin NMTOKEN #REQUIRED>
        <!ATTLIST t2_calibration info NMTOKEN #REQUIRED>
        <!ATTLIST t2_calibration valueUnit NMTOKEN #REQUIRED>
        <!ATTLIST t2_calibration timeUnit NMTOKEN #REQUIRED>
        <!ATTLIST t2_calibration unit NMTOKEN #REQUIRED>
        <!ELEMENT t2_ball (t2_prop,t2_linked_prop,t2_annot,t2_ball_ob)>
        <!ATTLIST t2_ball oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_ball layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_ball transform NMTOKEN #REQUIRED>
        <!ATTLIST t2_ball style NMTOKEN #REQUIRED>
        <!ATTLIST t2_ball locked NMTOKEN #REQUIRED>
        <!ATTLIST t2_ball visible NMTOKEN #REQUIRED>
        <!ATTLIST t2_ball title NMTOKEN #REQUIRED>
        <!ATTLIST t2_ball links NMTOKEN #REQUIRED>
        <!ATTLIST t2_ball composite NMTOKEN #REQUIRED>
        <!ATTLIST t2_ball fill NMTOKEN #REQUIRED>
        <!ELEMENT t2_ball_ob EMPTY>
        <!ATTLIST t2_ball_ob x NMTOKEN #REQUIRED>
        <!ATTLIST t2_ball_ob y NMTOKEN #REQUIRED>
        <!ATTLIST t2_ball_ob r NMTOKEN #REQUIRED>
        <!ATTLIST t2_ball_ob layer_id NMTOKEN #REQUIRED>
        <!ELEMENT t2_label (t2_prop,t2_linked_prop,t2_annot)>
        <!ATTLIST t2_label oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_label layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_label transform NMTOKEN #REQUIRED>
        <!ATTLIST t2_label style NMTOKEN #REQUIRED>
        <!ATTLIST t2_label locked NMTOKEN #REQUIRED>
        <!ATTLIST t2_label visible NMTOKEN #REQUIRED>
        <!ATTLIST t2_label title NMTOKEN #REQUIRED>
        <!ATTLIST t2_label links NMTOKEN #REQUIRED>
        <!ATTLIST t2_label composite NMTOKEN #REQUIRED>
        <!ELEMENT t2_filter EMPTY>
        <!ELEMENT t2_patch (t2_prop,t2_linked_prop,t2_annot,ict_transform,ict_transform_list,t2_filter)>
        <!ATTLIST t2_patch oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch transform NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch style NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch locked NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch visible NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch title NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch links NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch composite NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch file_path NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch original_path NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch type NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch false_color NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch ct NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch o_width NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch o_height NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch min NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch max NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch o_width NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch o_height NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch pps NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch mres NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch ct_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_patch alpha_mask_id NMTOKEN #REQUIRED>
        <!ELEMENT t2_pipe (t2_prop,t2_linked_prop,t2_annot)>
        <!ATTLIST t2_pipe oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_pipe layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_pipe transform NMTOKEN #REQUIRED>
        <!ATTLIST t2_pipe style NMTOKEN #REQUIRED>
        <!ATTLIST t2_pipe locked NMTOKEN #REQUIRED>
        <!ATTLIST t2_pipe visible NMTOKEN #REQUIRED>
        <!ATTLIST t2_pipe title NMTOKEN #REQUIRED>
        <!ATTLIST t2_pipe links NMTOKEN #REQUIRED>
        <!ATTLIST t2_pipe composite NMTOKEN #REQUIRED>
        <!ATTLIST t2_pipe d NMTOKEN #REQUIRED>
        <!ATTLIST t2_pipe p_width NMTOKEN #REQUIRED>
        <!ATTLIST t2_pipe layer_ids NMTOKEN #REQUIRED>
        <!ELEMENT t2_polyline (t2_prop,t2_linked_prop,t2_annot)>
        <!ATTLIST t2_polyline oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_polyline layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_polyline transform NMTOKEN #REQUIRED>
        <!ATTLIST t2_polyline style NMTOKEN #REQUIRED>
        <!ATTLIST t2_polyline locked NMTOKEN #REQUIRED>
        <!ATTLIST t2_polyline visible NMTOKEN #REQUIRED>
        <!ATTLIST t2_polyline title NMTOKEN #REQUIRED>
        <!ATTLIST t2_polyline links NMTOKEN #REQUIRED>
        <!ATTLIST t2_polyline composite NMTOKEN #REQUIRED>
        <!ATTLIST t2_polyline d NMTOKEN #REQUIRED>
        <!ELEMENT t2_profile (t2_prop,t2_linked_prop,t2_annot)>
        <!ATTLIST t2_profile oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_profile layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_profile transform NMTOKEN #REQUIRED>
        <!ATTLIST t2_profile style NMTOKEN #REQUIRED>
        <!ATTLIST t2_profile locked NMTOKEN #REQUIRED>
        <!ATTLIST t2_profile visible NMTOKEN #REQUIRED>
        <!ATTLIST t2_profile title NMTOKEN #REQUIRED>
        <!ATTLIST t2_profile links NMTOKEN #REQUIRED>
        <!ATTLIST t2_profile composite NMTOKEN #REQUIRED>
        <!ATTLIST t2_profile d NMTOKEN #REQUIRED>
        <!ELEMENT t2_area_list (t2_prop,t2_linked_prop,t2_annot,t2_area)>
        <!ATTLIST t2_area_list oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_area_list layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_area_list transform NMTOKEN #REQUIRED>
        <!ATTLIST t2_area_list style NMTOKEN #REQUIRED>
        <!ATTLIST t2_area_list locked NMTOKEN #REQUIRED>
        <!ATTLIST t2_area_list visible NMTOKEN #REQUIRED>
        <!ATTLIST t2_area_list title NMTOKEN #REQUIRED>
        <!ATTLIST t2_area_list links NMTOKEN #REQUIRED>
        <!ATTLIST t2_area_list composite NMTOKEN #REQUIRED>
        <!ATTLIST t2_area_list fill_paint NMTOKEN #REQUIRED>
        <!ELEMENT t2_area (t2_path)>
        <!ATTLIST t2_area layer_id NMTOKEN #REQUIRED>
        <!ELEMENT t2_path EMPTY>
        <!ATTLIST t2_path d NMTOKEN #REQUIRED>
        <!ELEMENT t2_dissector (t2_prop,t2_linked_prop,t2_annot,t2_dd_item)>
        <!ATTLIST t2_dissector oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_dissector layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_dissector transform NMTOKEN #REQUIRED>
        <!ATTLIST t2_dissector style NMTOKEN #REQUIRED>
        <!ATTLIST t2_dissector locked NMTOKEN #REQUIRED>
        <!ATTLIST t2_dissector visible NMTOKEN #REQUIRED>
        <!ATTLIST t2_dissector title NMTOKEN #REQUIRED>
        <!ATTLIST t2_dissector links NMTOKEN #REQUIRED>
        <!ATTLIST t2_dissector composite NMTOKEN #REQUIRED>
        <!ELEMENT t2_dd_item EMPTY>
        <!ATTLIST t2_dd_item radius NMTOKEN #REQUIRED>
        <!ATTLIST t2_dd_item tag NMTOKEN #REQUIRED>
        <!ATTLIST t2_dd_item points NMTOKEN #REQUIRED>
        <!ELEMENT t2_stack (t2_prop,t2_linked_prop,t2_annot,(iict_transform|iict_transform_list)?)>
        <!ATTLIST t2_stack oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_stack layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_stack transform NMTOKEN #REQUIRED>
        <!ATTLIST t2_stack style NMTOKEN #REQUIRED>
        <!ATTLIST t2_stack locked NMTOKEN #REQUIRED>
        <!ATTLIST t2_stack visible NMTOKEN #REQUIRED>
        <!ATTLIST t2_stack title NMTOKEN #REQUIRED>
        <!ATTLIST t2_stack links NMTOKEN #REQUIRED>
        <!ATTLIST t2_stack composite NMTOKEN #REQUIRED>
        <!ATTLIST t2_stack file_path CDATA #REQUIRED>
        <!ATTLIST t2_stack depth CDATA #REQUIRED>
        <!ELEMENT t2_tag EMPTY>
        <!ATTLIST t2_tag name NMTOKEN #REQUIRED>
        <!ATTLIST t2_tag key NMTOKEN #REQUIRED>
        <!ELEMENT t2_node (t2_area*,t2_tag*)>
        <!ATTLIST t2_node x NMTOKEN #REQUIRED>
        <!ATTLIST t2_node y NMTOKEN #REQUIRED>
        <!ATTLIST t2_node lid NMTOKEN #REQUIRED>
        <!ATTLIST t2_node c NMTOKEN #REQUIRED>
        <!ATTLIST t2_node r NMTOKEN #IMPLIED>
        <!ELEMENT t2_treeline (t2_node*,t2_prop,t2_linked_prop,t2_annot)>
        <!ATTLIST t2_treeline oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_treeline layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_treeline transform NMTOKEN #REQUIRED>
        <!ATTLIST t2_treeline style NMTOKEN #REQUIRED>
        <!ATTLIST t2_treeline locked NMTOKEN #REQUIRED>
        <!ATTLIST t2_treeline visible NMTOKEN #REQUIRED>
        <!ATTLIST t2_treeline title NMTOKEN #REQUIRED>
        <!ATTLIST t2_treeline links NMTOKEN #REQUIRED>
        <!ATTLIST t2_treeline composite NMTOKEN #REQUIRED>
        <!ELEMENT t2_areatree (t2_node*,t2_prop,t2_linked_prop,t2_annot)>
        <!ATTLIST t2_areatree oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_areatree layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_areatree transform NMTOKEN #REQUIRED>
        <!ATTLIST t2_areatree style NMTOKEN #REQUIRED>
        <!ATTLIST t2_areatree locked NMTOKEN #REQUIRED>
        <!ATTLIST t2_areatree visible NMTOKEN #REQUIRED>
        <!ATTLIST t2_areatree title NMTOKEN #REQUIRED>
        <!ATTLIST t2_areatree links NMTOKEN #REQUIRED>
        <!ATTLIST t2_areatree composite NMTOKEN #REQUIRED>
        <!ELEMENT t2_connector (t2_node*,t2_prop,t2_linked_prop,t2_annot)>
        <!ATTLIST t2_connector oid NMTOKEN #REQUIRED>
        <!ATTLIST t2_connector layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_connector transform NMTOKEN #REQUIRED>
        <!ATTLIST t2_connector style NMTOKEN #REQUIRED>
        <!ATTLIST t2_connector locked NMTOKEN #REQUIRED>
        <!ATTLIST t2_connector visible NMTOKEN #REQUIRED>
        <!ATTLIST t2_connector title NMTOKEN #REQUIRED>
        <!ATTLIST t2_connector links NMTOKEN #REQUIRED>
        <!ATTLIST t2_connector composite NMTOKEN #REQUIRED>
        <!ELEMENT t2_prop EMPTY>
        <!ATTLIST t2_prop key NMTOKEN #REQUIRED>
        <!ATTLIST t2_prop value NMTOKEN #REQUIRED>
        <!ELEMENT t2_linked_prop EMPTY>
        <!ATTLIST t2_linked_prop target_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_linked_prop key NMTOKEN #REQUIRED>
        <!ATTLIST t2_linked_prop value NMTOKEN #REQUIRED>
        <!ELEMENT t2_annot EMPTY>
        <!ELEMENT t2_display EMPTY>
        <!ATTLIST t2_display id NMTOKEN #REQUIRED>
        <!ATTLIST t2_display layer_id NMTOKEN #REQUIRED>
        <!ATTLIST t2_display x NMTOKEN #REQUIRED>
        <!ATTLIST t2_display y NMTOKEN #REQUIRED>
        <!ATTLIST t2_display magnification NMTOKEN #REQUIRED>
        <!ATTLIST t2_display srcrect_x NMTOKEN #REQUIRED>
        <!ATTLIST t2_display srcrect_y NMTOKEN #REQUIRED>
        <!ATTLIST t2_display srcrect_width NMTOKEN #REQUIRED>
        <!ATTLIST t2_display srcrect_height NMTOKEN #REQUIRED>
        <!ATTLIST t2_display scroll_step NMTOKEN #REQUIRED>
        <!ATTLIST t2_display c_alphas NMTOKEN #REQUIRED>
        <!ATTLIST t2_display c_alphas_state NMTOKEN #REQUIRED>
        <!ATTLIST t2_display filter_enabled NMTOKEN #REQUIRED>
        <!ATTLIST t2_display filter_min_max_enabled NMTOKEN #REQUIRED>
        <!ATTLIST t2_display filter_min NMTOKEN #REQUIRED>
        <!ATTLIST t2_display filter_max NMTOKEN #REQUIRED>
        <!ATTLIST t2_display filter_invert NMTOKEN #REQUIRED>
        <!ATTLIST t2_display filter_clahe_enabled NMTOKEN #REQUIRED>
        <!ATTLIST t2_display filter_clahe_block_size NMTOKEN #REQUIRED>
        <!ATTLIST t2_display filter_clahe_histogram_bins NMTOKEN #REQUIRED>
        <!ATTLIST t2_display filter_clahe_max_slope NMTOKEN #REQUIRED>
        <!ELEMENT ict_transform EMPTY>
        <!ATTLIST ict_transform class CDATA #REQUIRED>
        <!ATTLIST ict_transform data CDATA #REQUIRED>
        <!ELEMENT iict_transform EMPTY>
        <!ATTLIST iict_transform class CDATA #REQUIRED>
        <!ATTLIST iict_transform data CDATA #REQUIRED>
        <!ELEMENT ict_transform_list (ict_transform|iict_transform)*>
        <!ELEMENT iict_transform_list (iict_transform*)>
    ] >

    <trakem2>
        <project 
            id="0"
            title="Project"
    """)
    return header


def create_footer():
    """Generate footer for xml file"""
    footer = dedent("""
        </t2_layer_set>
    </trakem2>
    """)
    return footer
