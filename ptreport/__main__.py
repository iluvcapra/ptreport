"""
main
"""
from typing import Dict, Iterable, Tuple, List
import sys
import optparse
import re

from grpc.aio import UsageError
# from grpc import StatusCode

from ptulsconv.docparser import parse_document
from ptulsconv.docparser.doc_entity import Fraction, HeaderDescriptor, \
        TrackDescriptor, TrackClipDescriptor
from ptsl import open_engine

# from sys import stdout

def fetch_session_data(tc_format: str = "tc"):
    with open_engine(company_name="ptreport developers",
                     application_name="ptreport") as engine:

        builder = engine.export_session_as_text()
        builder.include_markers()
        builder.include_track_edls()
        builder.selected_tracks_only()
        builder.dont_show_crossfades()
        builder.time_type(tc_format)

        session_data = builder.export_string()
        return parse_document(session_data)


def emit_groff_header(session_name, output_stream=sys.stdout):
    output_stream.write(f"""
.eo
.TI {session_name}
.de MARK 
.   XP
.   UL \\$1
.   br 
..
.de RANGE 
.   XP
.   UL "\\$1 \\[->] \\$2"
.   br 
..
.nr PD 1v
.nr PI 5n 
.ta 10n 
.ec
""")


def emit_text_line(text: str, substitutions: Dict[str, str] = {},
                   output_stream=sys.stdout):

    for k in substitutions.keys():
        text = text.replace(k, substitutions[k])

    output_stream.write(text.strip(" ") + "\n")


def emit_clip_entry(session: HeaderDescriptor, track: TrackDescriptor,
                    clip: TrackClipDescriptor, output_stream=sys.stdout):

    clip_name = clip.clip_name

    output_stream.write(f".ds start_time {clip.start_timecode}\n")
    output_stream.write(f".ds finish_time {clip.finish_timecode}\n")
    output_stream.write(f".ds track_name {track.name}\n")

    substitutions = {
        '$session': session.session_name,
        '$i': clip.start_timecode,
        '$o': clip.finish_timecode,
        '$track': track.name,
    }
    if clip_name.startswith("-"):
        # Skip case, clip will not have an effect on the output.
        emit_text_line(".\\\" OMIITED CLIP: " + clip_name[1:],
                       substitutions, output_stream=output_stream)

    elif clip_name.startswith("#"):
        # Insert a numbered header
        # ".NH"
        m = re.match("^(#+)(.*)$", clip_name)
        if m:
            level = min(len(m[1]), 5)
            text = m[2]
            output_stream.write(f".NH {level}\n")
            emit_text_line(text, substitutions, output_stream=output_stream)

    elif clip_name.startswith("%"):
        # Insert an un-numbered header
        # ".SH"
        m = re.match("^(%+)(.*)$", clip_name)
        if m:
            level = min(len(m[1]), 5)
            text = m[2]
            output_stream.write(f".SH {level}\n")
            emit_text_line(text, substitutions, output_stream=output_stream)
    
    elif clip_name.startswith("["):
        # insert a non-indent paragraph
        # ".LP"
        output_stream.write(".LP\n")
        emit_text_line(clip_name[1:], substitutions, 
                       output_stream=output_stream)
    
    elif clip_name.startswith("]"):
        # insert an indented paragraph 
        # ".PP"
        output_stream.write(".PP\n")
        emit_text_line(clip_name[1:], substitutions,
                       output_stream=output_stream)

    elif clip_name.startswith("*"):
        # insert a bulleted paragraph
        output_stream.write(".IP \\[bu]\n")
        emit_text_line(clip_name[1:], substitutions, 
                       output_stream=output_stream)

    elif clip_name.startswith("!"):
        # Literal case, clip text will be inserted literally into the document
        # Every subsquent exclamati0on point will be replaced with a newline.
        # Use the groff \u0021 escape if you need to inseert an exclamation 
        # point.
        for line in clip_name[1:].split("!"):
            emit_text_line(line, substitutions,
                           output_stream=output_stream)

    elif clip_name.startswith(">"):
        # Insert the clip's text as a blockquote
        # ".BQ .BE"
        output_stream.write(".QS\n")
        emit_text_line(clip_name[1:],
                       substitutions,
                       output_stream=output_stream)
        output_stream.write(".QE\n")

    elif clip_name.startswith("/"):
        # Insert a formatted element with the clip's start and end time
        # ".RANGE"
        output_stream.write(f".RANGE \"{clip.start_timecode}\" "
                            f"\"{clip.finish_timecode}\"\n"
                            f"\"{clip.clip_name[1:]}\"")

    else:
        # By default, insert a formatted element with the clip's start time
        output_stream.write(f".MARK \"{clip.start_timecode}\"\n"
                            f"\"{clip_name}\" \n")

def sort_time_track(
        i: Iterable[Tuple[TrackDescriptor, 
                          TrackClipDescriptor, Fraction]]) -> \
    List[Tuple[TrackDescriptor, TrackClipDescriptor, Fraction]]:

    return sorted(
        sorted(i, 
               key=lambda x : x[0].index),
        key=lambda x: x[2]
    )


def typeset(tc_format: str = "tc"):
    document = fetch_session_data(tc_format=tc_format)

    emit_groff_header(document.header.session_name)

    sort_mode = sort_time_track

    for track, track_clip in map(lambda x: (x[0], x[1]), 
                                 sort_mode(
                                 map(lambda x: (x[0], x[1], x[2]),
                                     document.track_clips_timed()
                                     ))):
        emit_clip_entry(document.header, track, track_clip)

    # for track, track_clip, _, _, _ in document.track_clips_timed():
    #     emit_clip_entry(document.header, track, track_clip)


if __name__ == "__main__":

    opts = optparse.OptionParser()
    opts.set_defaults(tc_format='tc')

    formats_group = optparse.OptionGroup(opts, title="Output Time Formats")
    formats_group.add_option("--timecode", dest='tc_format',
                             help="Print clip start and finish as "
                             "timecodes (this is the default)",
                             action='store_const', const='tc')
    formats_group.add_option("--feet-frames", dest="tc_format",
                             help="Print clip start and finish in feet+frames"
                             " format",
                             action='store_const', const='feet+frames')
    formats_group.add_option("--min-secs", dest="tc_format",
                             help="Print clip start and finish in mins:secs "
                             "format",
                             action='store_const', const='min:sec')
    formats_group.add_option("--bars-beats", dest="tc_format",
                             help="Print clip start and finish in bars+beats "
                             "format",
                             action='store_const', const='bars+beats')

    opts.add_option_group(formats_group)

    (options, args) = opts.parse_args()

    try:
        typeset(tc_format=options.tc_format)
    except UsageError as e:
        sys.exit(2)
