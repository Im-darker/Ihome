from flask_script import Manager
from Ihome import create_app, db
from flask_migrate import Migrate, MigrateCommand

# 创建app应用对象
app = create_app("deve")
manager = Manager(app)
Migrate(app, db)
manager.add_command("db", MigrateCommand)


if __name__ == '__main__':
    manager.run()