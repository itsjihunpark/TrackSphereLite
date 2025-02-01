# TrackSphereLite

## Installation

follow this first
https://forums.raspberrypi.com/viewtopic.php?t=361758

First clone the project at the directory of choice and cd into it.

```bash
git clone https://github.com/itsjihunpark/TrackSphereLite.git
```

```bash
cd TrackSphereLite
```

To run this server, you must first install a few libraries.

Before installing any libraries, you must first create a python virtual environment. To find out more about virtual environments ([Python doc](https://docs.python.org/3/library/venv.html))

To create a virtual environment. The below creates a virtual environment named .venv

```bash
python -m venv .venv
```

Once the above runs, you must activate the virtual environment. Keep in mind that it is a backslash.

```bash
.venv\Scripts\activate
```

Once activated, to install required libraries, run

```bash
pip install -r requirements.txt
```

Now you are ready to run the application.

## Usage

Before running the application, you must always activate the virtual environment.

```bash
cd TrackSphereLite
```

```bash
.venv\Scripts\activate
```

Once activated run

```bash
.venv\Scripts\activate
```

```bash
flask --app TrackSphereLite run --debug
```

The app should be running by now. If its not working contact Jihun, he can help you with this ([some way to get in contact with jihun :)](mailto:jihunpark0989@gmail.com))

## License

[MIT](https://choosealicense.com/licenses/mit/)
