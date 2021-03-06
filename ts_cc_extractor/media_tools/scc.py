#!/usr/bin/env python
"""Parser and writer of SCC (Scenarist) files. The parser includes CEA608 parsing.

This format basically contains pairs of CEA-608 bytes.
Reference: http://www.theneitherworld.com/mcpoodle/SCC_TOOLS/DOCS/SCC_FORMAT.HTML
"""

# The copyright in this software is being made available under the BSD License,
# included below. This software may be subject to other third party and contributor
# rights, including patent rights, and no such rights are granted under this license.
#
# Copyright (c) 2016, Dash Industry Forum.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#  * Redistributions of source code must retain the above copyright notice, this
#  list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation and/or
#  other materials provided with the distribution.
#  * Neither the name of Dash Industry Forum nor the names of its
#  contributors may be used to endorse or promote products derived from this software
#  without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY
#  EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
#  IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
#  INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
#  NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#  WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.

import io

from . import cea608


def old_div(a, b):
    if isinstance(a, int) and isinstance(b, int):
        return a // b
    return a / b


class SccParser(object):
    "Parser of SCC files."

    def __init__(self, file_handle, outputFilter1=None, outputFilter2=None, field=1):
        self.file_handle = file_handle
        self.field = field
        self.cea608_field_processor = cea608.Cea608FieldProcessor(self.field, outputFilter1, outputFilter2)
        self.parse()
        self.close()

    def parse(self):
        "Parse the file given by self.file_handle."
        header = self.file_handle.readline()
        header = header.rstrip()
        assert(header == "Scenarist_SCC V1.0")
        while True:
            if not self.read_empty_line():
                break
            lineData = self.parse_data_line()
            if not lineData:
                break
            (time_data, _, cea_data) = lineData
            for d in cea_data:
                self.cea608_field_processor.add_data(d, time_data)

    def read_empty_line(self):
        "Read a line return True if it was empty."
        line = self.file_handle.readline()
        if not line:
            return False
        assert(line.strip() == "")
        return True

    def parse_data_line(self):
        "Parse a line which looks like 01:02:53:14	94ae 94ae 9420"
        line = self.file_handle.readline().strip()
        if not line:
            return None
        data = line.strip().split()
        time_data = data[0]
        cea_data = [(int("0x" + c[0:2], 16), int("0x" + c[2:4], 16)) for c in data[1:]]
        return (time_data, cea_data, cea_data)

    def close(self):
        "Close generators"
        self.cea608_field_processor.close()


class SccWriter(object):
    """Collect CEA-608 and write SCC file for a channel.

    Make filename given base. No file if no data.
    Lines are sorted according to time stamp to handle B-frames.
    """

    def __init__(self, base_name=None, channel=0, cc_files=None):
        self.file_handle = None
        self.cc_files = cc_files
        self.base_name = base_name
        self.channel = channel
        self.pts_offset = None
        self.data_sorter = DataSorter()
        self.written_header = False
        self.cea608_field_processor = cea608.Cea608FieldProcessor(channel)

    def get_cc_summary(self):
        "Get summary of CEA-608 data."
        cc = self.cea608_field_processor.get_cc_summary()
        return cc

    def calc_time_string(self, new_pts):
        "Calculate time string in scenarist format. This is done for 30Hz."
        delta_time = new_pts - self.pts_offset
        if delta_time < -1 * (1 << 32):
            self.pts_offset -= 1 << 33
            print("WARNING: PTS wrap-around")
            delta_time = new_pts - self.pts_offset
        r_time = delta_time
        hours = old_div(r_time, 3600 * 90000)
        r_time = r_time - hours * (3600 * 90000)
        minutes = old_div(r_time, 60 * 90000)
        r_time = r_time - minutes * (60 * 90000)
        seconds = old_div(r_time, 90000)
        r_time = r_time - seconds * 90000
        frames = old_div(r_time, 3000)  # 30Hz
        return "%02d:%02d:%02d:%02d" % (hours, minutes, seconds, frames)

    def add_data(self, byte_pair, pts_time):
        "Add a pair of bytes for a given pts_time."
        if not self.file_handle and self.base_name and self.cc_files is not None:
            self.file_handle = io.BytesIO()
            self.file_handle.write(b"Scenarist_SCC V1.0")
            self.written_header = True
        self.data_sorter.add_data(pts_time, byte_pair)
        self.write_lines()

    def write_lines(self, sorting_overlap=5):
        "Write lines in scenarist file."
        data_list = self.data_sorter.retrieve_data(sorting_overlap)

        for data_line in data_list:
            pts_time, data = data_line
            if self.pts_offset is None:
                self.pts_offset = pts_time
            line = "%s" % self.calc_time_string(pts_time)
            if line[0] == "-":
                print("WARNING: Negative timestamp for SCC %s" % line)
                continue
            for byte_pair in data:
                line += (" %02x%02x" % byte_pair)
                self.cea608_field_processor.add_data(byte_pair, pts_time)
            if self.file_handle:
                self.file_handle.write(str.encode("\n\n%s" % line))

    def close(self):
        "Write out the last data and close file handle."
        self.write_lines(sorting_overlap=0)
        if self.file_handle:
            self.file_handle.write(b"\n")
            self.file_handle.flush()
            scc_content = self.file_handle.getvalue()
            cc_file = {
                'name': self.base_name,
                'channel': self.channel,
                'content': scc_content.decode('utf-8'),
            }
            self.cc_files.append(cc_file)
            self.file_handle.close()
            self.file_handle = None

    def has_pts_offset(self):
        if self.pts_offset is not None:
            return True
        return False

    def set_pts_offset(self, pts_offset):
        self.pts_offset = pts_offset


class DataSorter(object):
    """Keeps data of form [(time, data)] sorted.

    Extract with sorting overlap, to make sure that later data is not earlier."""

    def __init__(self):
        self.last_timestamp = None
        self.data_list = []
        self.last_data = None

    def add_data(self, timestamp, data):
        "Add data with timestamp."
        if timestamp != self.last_timestamp:
            self.last_data = (timestamp, [data])
            self.data_list.append(self.last_data)
            self.last_timestamp = timestamp
        else:
            self.last_data[1].append(data)

    def retrieve_data(self, sorting_overlap=5):
        "Retrieve sorted data, except last sorting_overlap items."
        # print "Sorting %s" % sorting_overlap
        self.data_list.sort()
        if sorting_overlap > 0:
            retrieved_data = self.data_list[:-sorting_overlap]
            self.data_list = self.data_list[-sorting_overlap:]
        else:
            retrieved_data = self.data_list
            self.data_list = []
        return retrieved_data
