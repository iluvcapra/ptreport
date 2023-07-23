"""
main
"""
import re
from typing import Dict
# from fractions import Fraction

from ptulsconv.docparser import parse_document
from ptulsconv.docparser.doc_entity import MarkerDescriptor, TrackDescriptor, \
    TrackClipDescriptor, SessionDescriptor
from ptsl import open_engine

# from sys import stdout
import sys


def fetch_session_data():
    with open_engine(company_name="ptreport developers",
                     application_name="ptreport") as engine:

        builder = engine.export_session_as_text()
        builder.include_markers()
        builder.include_track_edls()
        builder.selected_tracks_only()
        builder.dont_show_crossfades()
        builder.time_type("tc")

        session_data = builder.export_string()
        return parse_document(session_data)


def emit_groff_header(session_name, output_stream=sys.stdout):
    output_stream.write(f".TI {session_name}\n")
    output_stream.write(""".de ei
.XP
.I "\\\\$1"
.br 
\\\\$2
..
""")
    output_stream.write(""".de eio 
.XP
.I "\\\\$1 \\\\[->] \\\\$2"
.br 
\\\\$3
..
""")
    output_stream.write(".fam H\n")
    output_stream.write(f".nr PD 1v\n")
    output_stream.write(f".nr PI 5n\n")
    output_stream.write(".ta 10n\n")
    output_stream.write(f".SH 1\n.LG\n.LG\n{session_name}\n.NL\n")


def emit_text_line(text: str,
                   substitutions: Dict[str, str] = {},
                   output_stream=sys.stdout):

    for k in substitutions.keys():
        text = text.replace(k, substitutions[k])

    output_stream.write(text + "\n")


def emit_clip_entry(track: TrackDescriptor,
                    clip: TrackClipDescriptor,
                    output_stream=sys.stdout):

    clip_name = clip.clip_name
    substitutions = {
        '$start': clip.start_timecode,
        '$finish': clip.finish_timecode,
        '$track_name': track.name,
    }
    if clip_name.startswith("-"):
        # Skip case, clip will not have an effect on the output.
        emit_text_line(".\\\" OMIITED CLIP: " + clip_name[1:],
                       substitutions)

    elif clip_name.startswith("!"):
        # Literal case, clip text will be inserted literally into the document
        emit_text_line(clip_name[1:], substitutions,
                       output_stream=output_stream)

    elif clip_name.startswith(">"):
        # Insert the clip's text as a blockquote
        output_stream.write(".QS\n")
        emit_text_line(clip_name[1:],
                       substitutions,
                       output_stream=output_stream)
        output_stream.write(".QE\n")

    elif clip_name.startswith("/"):
        # Insert a formatted element with the clip's start and end time
        output_stream.write(f".eio \"{clip.start_timecode}\" "
            f"\"{clip.finish_timecode}\" \"{clip.clip_name[1:]}\"")

    else:
        # By default, insert a formatted element with the clip's start time
        output_stream.write(f".ei \"{clip.start_timecode}\" \"{clip_name}\" \n" )


def main():
    document = fetch_session_data()

    emit_groff_header(document.header.session_name)

    for track, track_clip, _, _, _ in document.track_clips_timed():
        emit_clip_entry(track, track_clip)


if __name__ == "__main__":
    main()
