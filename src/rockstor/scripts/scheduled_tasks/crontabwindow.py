"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
This file is part of RockStor.

RockStor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

RockStor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from datetime import datetime, time

# Crontabwindow created as a separate module to avoid code duplication on
# snapshots and scrubs tasks


def crontab_range(range):
    inrange = False
    # logger.debug('Crontab window is %s' % range)
    if range == "*-*-*-*-*-*":
        # on range value equal to always (*-*-*-*-*-*), always exec tasks
        inrange = True
    else:
        today = datetime.today()
        today_time = today.time()
        today_weekday = today.weekday()
        range_windows = range.split("-")
        hour_start = int(range_windows[0]) if range_windows[0] != "*" else 0
        mins_start = int(range_windows[1]) if range_windows[1] != "*" else 0
        hour_stop = int(range_windows[2]) if range_windows[2] != "*" else 23
        mins_stop = int(range_windows[3]) if range_windows[3] != "*" else 59
        day_start = int(range_windows[4]) if range_windows[4] != "*" else 0
        day_stop = int(range_windows[5]) if range_windows[5] != "*" else 6
        time_start = time(hour_start, mins_start)
        time_stop = time(hour_stop, mins_stop, 59)

        # if crontab window isn't clockwise (unconvencional cron window)
        # current time/day will never be true on start <= current <= end so we
        # get it true if start <= current OR current <= end

        if hour_start <= hour_stop:
            intime = time_start <= today_time <= time_stop
        else:
            intime = time_start <= today_time or today_time <= time_stop

        if day_start <= day_stop:
            inday = day_start <= today_weekday <= day_stop
        else:
            inday = day_start <= today_weekday or today_weekday <= day_stop
        inrange = intime and inday
    return inrange
