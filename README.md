# ptreport

`ptreport` is a tool that generates reports in the groff typesetting language 
from [Pro Tools][pt] sessions, for example to create spotting lists or reports. 
`ptreport` uses [PTSL][ptsl] to connect directly to Pro Tools, without the 
need to export text from the session and allowing for enhanced data import.

[pt]: https://www.avid.com/pro-tools
[ptsl]: https://github.com/iluvcapra/py-ptsl

## How to Use 

Installing `ptreport` with `pip` will install a command-line tool that can be
invoked directly from a terminal. The tool will connect to Pro Tools with PTSL
and emit `groff(1)` commands to the standard output. These can be immediately 
piped to `groff(1)` for rendering to a device. 

```sh  
$ ptreport | groff -k -ms -Tpdf > output.pdf
```

At this time, the markup emitted by `ptreport` uses the [`groff_ms(7)`][ms] 
macro package. Pro Tools clip and track names are read as Unicode, thus the 
`-k` flag should be used.

For more information consult `man ptreport`.

[ms]: https://man7.org/linux/man-pages/man7/groff_ms.7.html
