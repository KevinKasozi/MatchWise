from sqlalchemy import create_engine
engine = create_engine("postgresql://postgres:postgres@localhost:5432/football_predictor")
print("Engine created successfully!") 