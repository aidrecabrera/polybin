from inference import InferencePipeline
from inference.core.interfaces.stream.sinks import render_boxes

pipeline = InferencePipeline.init(
    model_id="garbage-segregator-ndyo4/5", 
    video_reference=0, 
    on_prediction=render_boxes, 
)
pipeline.start()
pipeline.join()