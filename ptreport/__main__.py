"""
main
"""
import re
from typing import cast, List, Tuple
from fractions import Fraction

from ptulsconv.docparser import parse_document
from ptulsconv.docparser.doc_entity import MarkerDescriptor, TrackDescriptor, \
    ClipDescriptor, SessionDescriptor
from ptsl import open_engine

from sys import stdout
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


def sorted_document_events(document: SessionDescriptor) -> List[
        Tuple[str, Fraction, Tuple[
        TrackDescriptor, ClipDescriptor
        ] | MarkerDescriptor]]:

    sorted_clips = sorted(document.track_clips_timed(),
                          key=lambda x: x[2])

    sorted_clips_keyed = map(lambda x: ("Clip", x[2], x),
                             sorted_clips)

    sorted_markers = sorted(document.markers_timed(),
                            key=lambda x: x[1])

    sorted_markers_keyed = map(lambda x: ("Marker",
                                          x[1] + document.header.start_time,
                                          x),
                               sorted_markers)

    return sorted(list(sorted_clips_keyed) + list(sorted_markers_keyed),
                  key=lambda x: x[1])


def emit_groff_header(session_name, output_stream=sys.stdout):
    output_stream.write(f".TI {session_name}\n")
    output_stream.write(".fam H\n")
    output_stream.write(f".nr PD 1v\n")
    output_stream.write(f".nr PI 5n\n")
    output_stream.write(".ta 10n\n")
    output_stream.write(f".SH 1\n.LG\n.LG\n{session_name}\n.NL\n")


def emit_text_line(text: str, output_stream=sys.stdout):
    output_stream.write(text + "\n")


def emit_clip_entry(track: TrackDescriptor, clip: ClipDescriptor,
                    output_stream=sys.stdout):

    clip_name = clip.clip_name

    if clip_name.startswith("-"):
        # Skip case, clip will not have an effect on the output.
        emit_text_line(".\\\" OMIITED CLIP: " + clip_name[1:])

    elif clip_name.startswith("!"):
        # Literal case, clip text will be inserted literally into the document
        emit_text_line(clip_name[1:], output_stream)

    elif clip_name.startswith(">"):
        # Insert the clip's text as a blockquote
        output_stream.write(".QS\n")
        emit_text_line(clip_name[1:], output_stream)
        output_stream.write(".QE\n")

    else:
        output_stream.write(".XP\n")
        output_stream.write(f".I \"{clip.start_timecode} \\[->] "
                            f"{clip.finish_timecode}\"\n")
        output_stream.write(".br\n")
        m = re.match("^\\[(.+)\\]", track.name)
        if m:
            rubric = m[1]
            output_stream.write(f".B \"{rubric}:\"\n")

        output_stream.write(f"{clip_name}\n")


def emit_marker_entry(marker: MarkerDescriptor, output_stream=sys.stdout):
    pass
    # if marker.name.startswith("-"):
    #     pass
    #
    # elif marker.name.startswith("SH"):
    #     m = re.match("SH (\\d+) (.*)", marker.name)
    #     if m:
    #         output_stream.write(".nr VS +8\n")
    #         output_stream.write(f".SH {m[1]}\n")
    #         output_stream.write(f"{m[2]}\n")
    #         output_stream.write(".nr VS -8\n")
    # else:
    #     output_stream.write(".XP\n")
    #     output_stream.write(f".B \"{marker.location} \\[DI]\"\n")
    #     output_stream.write(".br\n")
    #     output_stream.write(f"{marker.name}\n")
    #
    # if len(marker.comments) > 0:
    #     output_stream.write(".QS\n")
    #     output_stream.write(f"{marker.comments}\n")
    #     output_stream.write(".QE\n")
    #


def main():
    document = fetch_session_data()

    emit_groff_header(document.header.session_name)

    sorted_events = sorted_document_events(document)

    for kind, _, event in sorted_events:
        if kind == 'Clip':
            event = cast(Tuple[TrackDescriptor, ClipDescriptor], event)
            track = cast(TrackDescriptor, event[0])
            clip = cast(ClipDescriptor, event[1])
            emit_clip_entry(track, clip)
        elif kind == 'Marker':
            event = cast(Tuple[MarkerDescriptor, Fraction], event)
            marker = event[0]
            emit_marker_entry(marker)


if __name__ == "__main__":
    main()
