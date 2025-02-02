from trackSphereLite.model.util import singleton
from flask import current_app, g
import sqlite3
from datetime import datetime
from trackSphereLite.model.Golfball import FlightedGolfball, RollingGolfball


@singleton
class DataAccess:

    def __init__(self):
         sqlite3.register_converter(
            "timestamp", lambda v: datetime.fromisoformat(v.decode())
        )
    
    def insert_new_user(self, username, password, name):
        db = self.__get_db()
        try:
            db.execute(
                "INSERT INTO Golfer (username, password, name) VALUES (?, ?, ?)", (username, password, name)
            )
            db.commit()
        except db.IntegrityError:
            error = f"User {username} is already signed up"
            return error
        else:
            return True

    def get_golfer_by_username(self, username):
        db = self.__get_db()      
        user = db.execute(
            'SELECT * FROM Golfer WHERE username = ?',(username,)
        ).fetchone()

        return user
    
    def get_golfer_by_golfer_id(self, golfer_id):
        db = self.__get_db()      
        user = db.execute(
            'SELECT * FROM Golfer WHERE golferID = ?',(golfer_id,)
        ).fetchone()

        return user

        
    def get_all_golf_swing_metrics_by_golfer_id(self, golfer_id):
        db = self.__get_db()      
        metrics = db.execute(
            'SELECT * FROM Golfball WHERE golferID = ?',(golfer_id,)
        ).fetchall()
        golfball_dict_list = []

        for metric in metrics:
            if metric['typeOfClub'] != "p":
                golfball = FlightedGolfball(metric['golfballID'], metric['swingEventTimestamp'].strftime("%Y-%m-%d %H:%M:%S"), 
                                        metric['typeOfClub'], metric['replaypath'], metric['velocityX'], metric['velocityY'], metric['velocityZ'])
            else:
                golfball = RollingGolfball(metric['golfballID'], metric['swingEventTimestamp'].strftime("%Y-%m-%d %H:%M:%S"), 
                                        metric['typeOfClub'], metric['replaypath'], metric['xPositions'], metric['yPositions'], metric['totalPuttTime'])
                print("model with rolling golfball")
            golfball_dict_list.append(golfball)

        return golfball_dict_list
    
    def get_all_golf_swing_metrics_by_golfballID(self, metricid_list):
        
        if len(metricid_list) == 1:
            metricid_list = '('+str(metricid_list[0])+')'
        db = self.__get_db()  
        metrics = db.execute(
            f'SELECT * FROM Golfball WHERE golfballID IN {metricid_list}'
        ).fetchall()
        golfball_dict_list = []
        for metric in metrics:
            if metric['typeOfClub'] != "p":
                golfball = FlightedGolfball(metric['golfballID'], metric['swingEventTimestamp'].strftime("%Y-%m-%d %H:%M:%S"), 
                                        metric['typeOfClub'], metric['replaypath'], metric['velocityX'], metric['velocityY'], metric['velocityZ'])
            else:
                golfball = RollingGolfball(metric['golfballID'], metric['swingEventTimestamp'].strftime("%Y-%m-%d %H:%M:%S"), 
                                        metric['typeOfClub'], metric['replaypath'], metric['xPositions'], metric['yPositions'], metric['totalPuttTime'])
                print("model with rolling golfball")
            golfball_dict_list.append(golfball)
        
        return golfball_dict_list 

    def get_all_replay_video_path_by_golfballID(self, metricid_list):
        
        if len(metricid_list) == 1:
            metricid_list = '('+str(metricid_list[0])+')'

        db = self.__get_db()  
        replaypaths = db.execute(
            f'SELECT replaypath FROM Golfball WHERE golfballID IN {metricid_list}'
        ).fetchall()
        replaypath_list = []
        for replaypath in replaypaths:
            replaypath_list.append(replaypath['replaypath'])
        
        return replaypath_list

    # DB UTILITY METHODS
    def init_app(self, app):
        # tells flask app to call close db connection after completing a request
        app.teardown_appcontext(self.__close_db)          

    def __get_db(self):
        # g is a special object that stores data that might be
        # accessed by multiple function during a request but not after

        if 'db' not in g: 
            g.db = sqlite3.connect(
                # current_app is a reference to the current flask application object
                # this is needed as flask application is created with an application factory
                current_app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row
        return g.db

    def __close_db(self, e=None):
        current_app.logger.info("RAN DB CONNECTION TEARDOWN")
        db = g.pop('db',None) 
        if db is not None:
            db.close()