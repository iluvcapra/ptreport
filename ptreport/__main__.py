"""
main
"""

from ptulsconv.docparser import parse_document
from ptsl import open_engine

from sys import stdout


def main():
    with open_engine(company_name="ptreport developers",
                     application_name="ptreport") as engine:

        builder = engine.export_session_as_text()
        builder.include_markers()
        builder.include_track_edls()
        builder.selected_tracks_only()
        builder.dont_show_crossfades()
        builder.time_type("tc")

        session_data = builder.export_string()
        document = parse_document(session_data)

        stdout.write(f".TI {document.header.session_name}\n")
        # stdout.write(f".TL {document.header.session_name}\n")
        stdout.write(f".nr PD 1v\n")
        stdout.write(f".nr PI 10n\n")
        stdout.write(".ta 10n\n")
        stdout.write(f".SH 1\n{document.header.session_name}\n")

        sorted_clips = sorted(document.track_clips_timed(),
                              key=lambda x: x[2])

        for track, clip, _, _, _ in sorted_clips:
            stdout.write(".XP\n")
            stdout.write(f".B \"{clip.start_timecode} \\[->] "
                         f"{clip.finish_timecode}\"\n")
            stdout.write(".br\n")
            stdout.write(f"{clip.clip_name}.\n")


if __name__ == "__main__":
    main()

