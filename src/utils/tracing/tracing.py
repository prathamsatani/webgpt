from phoenix.otel import register

class Tracer:
    def __init__(self, project_name: str):
        self.tracer_provider = register(
            project_name=project_name,
            auto_instrument=True
        )
    
    def get_tracer(self):
        return self.tracer_provider