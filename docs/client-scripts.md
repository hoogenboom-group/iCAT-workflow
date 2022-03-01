# Client Script Documentation

### PointMatchClient
```sh
Usage: java -cp <render-module>-standalone.jar
      org.janelia.render.client.PointMatchClient [options] canvas_1_URL
      canvas_2_URL [canvas_p_URL canvas_q_URL] ... (each URL pair identifies
      render parameters for canvas pairs)
  Options:
    --SIFTfdSize
      SIFT feature descriptor size: how many samples per row and column
      Default: 8
    --SIFTmaxScale
      SIFT maximum scale: minSize * minScale < size < maxSize * maxScale
      Default: 0.85
    --SIFTminScale
      SIFT minimum scale: minSize * minScale < size < maxSize * maxScale
      Default: 0.5
    --SIFTsteps
      SIFT steps per scale octave
      Default: 3
  * --baseDataUrl
      Base web service URL for data (e.g. http://host[:port]/render-ws/v1)
    --canvasGroupIdAlgorithm
      Algorithm for deriving canvas group ids
      Default: FIRST_TILE_SECTION_ID
      Possible Values: [FIRST_TILE_SECTION_ID, FIRST_TILE_Z, COLLECTION]
    --canvasIdAlgorithm
      Algorithm for deriving canvas ids
      Default: FIRST_TILE_ID
      Possible Values: [FIRST_TILE_ID, FIRST_TILE_Z, CANVAS_NAME]
    --clipHeight
      Number of full scale pixels to include in rendered clips of TOP/BOTTOM
      oriented montage tiles
    --clipWidth
      Number of full scale pixels to include in rendered clips of LEFT/RIGHT
      oriented montage tiles
  * --collection
      Match collection name
    --debugDirectory
      Directory to save rendered canvases for debugging (omit to keep rendered
      data in memory only)
    --fillWithNoise
      Fill each canvas image with noise before rendering to improve point
      match derivation
      Default: true
    --firstCanvasPosition
      When clipping, identifies the relative position of the first canvas to
      the second canvas
      Possible Values: [TOP, BOTTOM, LEFT, RIGHT]
    --help
      Display this note
    --matchFilter
      Identifies if and how matches should be filtered
      Default: SINGLE_SET
      Possible Values: [NONE, SINGLE_SET, CONSENSUS_SETS, AGGREGATED_CONSENSUS_SETS]
    --matchIterations
      Match filter iterations
      Default: 1000
    --matchMaxEpsilon
      Minimal allowed transfer error for match filtering
      Default: 20.0
    --matchMaxNumInliers
      Maximum number of inliers for match filtering
    --matchMaxTrust
      Reject match candidates with a cost larger than maxTrust * median cost
      Default: 3.0
    --matchMinInlierRatio
      Minimal ratio of inliers to candidates for match filtering
      Default: 0.0
    --matchMinNumInliers
      Minimal absolute number of inliers for match filtering
      Default: 4
    --matchModelType
      Type of model for match filtering
      Default: AFFINE
      Possible Values: [TRANSLATION, RIGID, SIMILARITY, AFFINE]
    --matchRod
      Ratio of distances for matches
      Default: 0.92
    --matchStorageFile
      File to store matches (omit if matches should be stored through web
      service)
    --numberOfThreads
      Number of threads to use for processing
      Default: 1
  * --owner
      Match collection owner
    --renderFileFormat
      Format for saved canvases (only relevant if debugDirectory is specified)
      Default: JPG
      Possible Values: [JPG, PNG, TIF]
    --renderScale
      Render canvases at this scale
      Default: 1.0
```

### BoxClient
```sh
Usage: java -cp <render-module>-standalone.jar
      org.janelia.render.client.BoxClient [options] Z values for layers to
      render
  Options:
  * --baseDataUrl
      Base web service URL for data (e.g. http://host[:port]/render-ws/v1)
    --binaryMask
      use binary mask (e.g. for DMG data)
      Default: false
    --createIGrid
      create an IGrid file
      Default: false
    --doFilter
      Use ad hoc filter to support alignment
      Default: false
    --filterListName
      Apply this filter list to all rendering (overrides doFilter option)
    --forceGeneration
      Regenerate boxes even if they already exist
      Default: false
    --format
      Format for rendered boxes
      Default: png
  * --height
      Height of each box
    --help
      Display this note
    --label
      Generate single color tile labels instead of actual tile images
      Default: false
    --maxLevel
      Maximum mipmap level to generate
      Default: 0
    --maxOverviewWidthAndHeight
      Max width and height of layer overview image (omit or set to zero to
      disable overview generation)
    --numberOfRenderGroups
      Total number of parallel jobs being used to render this layer (omit if
      only one job is being used)
  * --owner
      Stack owner
  * --project
      Stack project
    --renderGroup
      Index (1-n) that identifies portion of layer to render (omit if only one
      job is being used)
  * --rootDirectory
      Root directory for rendered tiles (e.g.
      /tier2/flyTEM/nobackup/rendered_boxes)
    --skipInterpolation
      skip interpolation (e.g. for DMG data)
      Default: false
  * --stack
      Stack name
  * --width
      Width of each box
```
