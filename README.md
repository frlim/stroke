Python 3 command line tool to run [a stroke triage model](https://github.com/aymannnn/stroke) on randomly generated patients at a set of provided locations<sup>[1](#footnote1)</sup>. Locations and adjacent hospitals must be provided, with appropriate pre-calculated travel times<sup>[2](#footnote2)</sup>.  Runs model using both generic hospital performance characteristics and provided specific characteristics for each hospital to allow analysis of the impact of including hospital performance in the model.

**Included demo input files use random hospital performance characteristics and do not reflect the performance of any real hospitals.**

### Usage ###

Dependencies are recorded in `stroke.yml`. From the root of the repo call the tool as

```
python3 main.py <hospital_file> <times_file> <options>
```

where `<hospital_file>` and `<times_file>` are relative paths to correctly formatted hospital and location files. Use `python3 main.py --help` for more information on options.

----
<a name="footnote1">1</a>: A [Swift implementation](https://github.com/eschenfeldt/stroke-multi) of the tool is also available.

<a name="footnote2">2</a>: A tool to generate these input files for locations and hospitals in the US (without hospital performance data), is available [here](https://github.com/eschenfeldt/stroke_locations)
