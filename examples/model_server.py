from chitra.serve import create_app


model = lambda x: x + 1
app = create_app(model, run=True)