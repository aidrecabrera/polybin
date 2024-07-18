from inference import InferencePipeline
from inference.core.interfaces.stream.sinks import render_boxes

pipeline = InferencePipeline.init(
    model_id="model_id/version",
    video_reference=0,
    on_prediction=render_boxes, # Function to run after each prediction
)
pipeline.start()
pipeline.join()