DROP TABLE IF EXISTS Golfer;
DROP TABLE IF EXISTS Golfball;

CREATE TABLE Golfer (
    golferID INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE Golfball (
    golfballID INTEGER PRIMARY KEY AUTOINCREMENT,
    golferID REFERENCES Golfer (golferID) NOT NULL,
    swingEventTimestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    typeOfClub TEXT NOT NULL,
    replaypath TEXT,
    velocityX DOUBLE,
    velocityY DOUBLE,
    velocityZ DOUBLE,
    positionsX TEXT,
    positionsY TEXT,
    positionsZ TEXT,
    totalPuttTime DOUBLE
);