from flaskblog import app, db

with app.app_context():
    # reflect all tables in the database, 
    # not just the ones that are defined in the models.py
    db.reflect()

    # delete all tables
    db.drop_all()

    # create new tables
    db.create_all()

print("Database created successfully!")