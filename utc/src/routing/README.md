<div id="top"></div>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <h3 align="center">Automated Planning</h3>
  <p align="center">
    Intelligent traffic routing with planner 
    <a href="https://fai.cs.uni-saarland.de/katz/papers/ipc2014a.pdf" target="_blank">Mercury</a>
    in PDDL language.
  </p>
</div>


<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-package">About The Package</a>
    </li>
    <li>
        <a href="#architecture">Architecture</a>
    </li>
    <li>
      <a href="#usage">Usage</a>
        <ul>
            <li><a href="#parameters">Parameters</a></li>
        </ul>
    </li>
    <li>
      <a href="#pddl-representation">PDDL representation</a>
        <ul>
            <li><a href="#domain">Domain</a></li>
            <li><a href="#problem">Problem</a></li>
            <li><a href="#problem">Result</a></li>
        </ul>
    </li>
  </ol>
</details>



<!-- ABOUT THE PACKAGE -->
## About The Package

This package implements traffic routing with the intention to reduce overall average travel time.
This is done by extracting vehicles from SUMO's simulation (or file in case of offline planning) in given time interval window
(this is usually 30 seconds). Then sub-network is created specific for the given vehicles, since often
we cannot directly use the original network because of it size. Afterwards the sub-network and vehicles get 
converted into a problem defined in PDDL language and saved as file (more information in ["PDDL"](#pddl-representation) section).

When we created problem file, we can use planner with appropriate PDDL [domain](../../data/domains/utc_allowed.pddl) file,
in this project planner [Mercury](https://fai.cs.uni-saarland.de/katz/papers/ipc2014a.pdf) is used, specifically the implementation
submitted to [2014 International Planning Competition](https://helios.hud.ac.uk/scommv/IPC-14/index.html). Mercury is given
time limit, which must be less than the original time window, since we are assuming vehicles communicate with a central system
(by using navigation, or similar device often found in modern vehicles) and give their location and destination in advance (time window) before
entering the road network. Other planner can be used, however it must be defined before in [pddl constants](../constants/static/pddl_constants.py) file.

If the planner was able to produce result, the new routes are converted back to original representation and given to vehicles
either in running simulation or saved to file, depending on the mode used to run planning. In case of online-planning we are running
simulation and extracting vehicles directly from it, this requires periodically saving and loading simulation states, otherwise
we do not know which vehicles are loaded in advance by X (time window) seconds. The advantage of this approach is that it more closely
models the real world, where we can expect to receive information about vehicles in real time, another one is that we do not need file with 
vehicles and their routes, as it might not be provided in traffic scenario (or there could be flows, probabilistic route choice etc.). 
For offline planning we take  advantage of having file with all vehicles and routes and extract vehicles directly from there, 
we can also leverage multi-processing, because we are assuming vehicle arrival to be independent of any delays etc. 
(for simplicity, since predicting vehicle arrival is hard). This  way we can generate all Pddl problem files and 
then plan multiple at once, greatly reducing overall time.

Finally, we can compare the original traffic scenario vs the new routed one with SUMO's vehicle statistical data, more 
about this can be read [here](https://sumo.dlr.de/docs/Simulation/Output/StatisticOutput.html).

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- Architecture -->
## Architecture



<!-- USAGE EXAMPLES -->
## Usage

The package can be used simply by passing the correct JSON configuration file, more about it's content in "Parameters" section.
```shell
python pddl_main.py -c [configuration file]
```


### Parameters
There are several parameters, that must be set manually by the user for the planning to work.
First, the user must have valid SUMO traffic scenario, for offline planning mode, the scenario must be in the project's folder structure and naming sense,
more about this is described in the [simulator](../simulator) package, otherwise we only require full path to SUMO's [configuration]()
file in the online mode.

As usual, the parameters are defined in JSON configuration file, which looks like [this](../../data/config/pddl_config.json) and
must satisfy schema's defined for each of its parts.

There are 3 main categories of options: initialization, planning and network. Each has its own schema, where basic constraints
for parameters are listed.

#### Initialization
1) Scenario: the name of traffic scenario, or full path to configuration file.
2) New scenario: name of new scenario, it will be created in this project's structure in the [scenarios](../../data/scenarios) directory.
3) Network: name or full path to road network we want the planning to be done on, it can be sub-network (region) of the original, 
in case the original is too large (for example obtained by [Gravitational clustering](../clustering)).
4) Mode: either "offline" or "online", as stated above.
5) Snapshot: optional parameter, path (or name) to simulation state file, which starts just before simulation (so that
the network already contains vehicles and is not empty). 

#### Planning
1) Window: the periodic interval of vehicle extraction (0-window, window-2*window, ...), usually 30 seconds.
2) Timeout: the total time for planner before it's execution is killed, should be less than window by few seconds.
3) Planner: name of the planner we want to use, must be defined in [pddl constants](../constants/static/pddl_constants.py) PLANNERS class.
4) Domain: name or full path of domain file, in case of name it must be defined in "[domains](../../data/domains)" directory. 
5) Keep results / problems / planner output: boolean values, set to true if we want to keep any of the PDDL files.


#### Network
1) Simplify: boolean value, set to true if we want simplification of the network to be used.
2) TopKA*: parameters related to [TopKA*](../graph) algorithm.
3) DBSCAN: parameters related to [Similarity clustering](../clustering) algorithm.

<p align="right">(<a href="#top">back to top</a>)</p>

<!-- PDDL representation -->
## PDDL representation

### Domain

### Problem

### Result



<p align="right">(<a href="#top">back to top</a>)</p>
