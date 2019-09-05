# system_monitoring_tool
Logs your systems cpu temperature.

## Install dependencies
`python -m pip install -r requirements.txt`

## Usage
To log the cpu temperature at current time use the `--log` flag.
To Schedule future logging use the `--schedule`.
To view the data use the `--view` flag (currently unsupported).

#### The Schedule flag
When using the Schedule flag some parameters are expected. You are going to have to pass at least a `--job_type` with value `intervall` or `cron` and then its up to you to decide how often or when it should log. If no time parameters are passed its going to loop over and over.

#### The log flag
The log flag is passed if you want a log the temperature of the system before the first shceduled log. If interval mode is used its going to delay untill your set time before the first data is aquired.

#### The view flag
Not yet implemented but is going to generate matplotlib graphs and/or print general data in terminal.

#### Using as a daemon with systemd
1: Edit the provided service file to your liking, at minimum provide path to python interpreter (full path to venv or just `python3` for system interpreter) and full path to the location of `cpu_temp.py`.\
2: Move the service file to your systemd/system directory (in ubunto derivatives `/etc/systemd/system`).\
3: `chmod 644 path/to/service_file.service`.\
4: `sudo systemctl daemon-reload`.\
5: `sudo systemctl enable cpu_temp.service`.

#### Run examples
For single log.\
`python cpu_temp.py --log`

To log every 30 second and on start of execution.\
`python cpu_temp.py --log --schedule --job_type interval --second 30`

To log at midnight.\
`python cpu_temp.py --schedule --job_type cron --hour 0`

## Future features
Improved CLI features for cron jobs and implemend functionality behind `--view` flag by matplotlib and/or simple print outs.
