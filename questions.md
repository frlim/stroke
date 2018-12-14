# Modeling Questions #

Collecting some open issues for the model that need to be resolved

## Treatment of Thrombectomy Capable certification ##

Should TSCs be treated like primaries, comprehensives, or a fusion of the two? One simple fusion possibility is that they act like comprehensives but cannot be selected as a transfer destination, but I have no idea if that's an accurate reflection of their capabilities.

## Transfers ##

Currently we treat primary and drip and ship as purely separate strategies, with the latter always incurring a transfer cost and the former never. Does this accurately capture the nature of transfers, which only happen in the case that EVT is necessary?

## Independence of intrahospital times ##

Since every hospital now has its own distribution, we need to decide whether the random intrahospital times are drawn independently or computed together. The former is perhaps more natural seeming but introduces significant variability, as lower-performing or more distant hospitals can randomly be the optimal choice because they hit the fast end of their distribution. The latter reduces variability by basing our judgement more on the distribution itself.

Drawing them independently feels more like an accurate representation of reality to me, and the increased variability is a reflection of the uncertainty of our approximation (though that uncertainty might be exaggerated by using uniform distributions if they don't accurately reflect the reality). However, it can be argued that we don't necessarily care as much about representing reality as we do about identifying the best choice given available data and thus should focus on the distributions rather than the randomness.

## Approximation of intrahospital time during transfers. ##

Currently we compute `onset_evt_ship` as
```
time_since_symptoms + primary.time + primary.door_to_needle + primary.transfer_time + transfer_to_puncture
```
where
```
transfer_to_puncture = comp.door_to_puncture - primary.door_to_needle
```
so `primary.door_to_needle` drops out entirely. This in itself is okay since primary door to needle time is accounted for in the `onset_needle_primary` part of `run_primary_then_ship`, but it does end up being kind of weird when we're comparing different primary centers to each other. Ideally we'd have real data on transfer times, but as it is we seem to be implicitly assuming primary hospitals with faster door to needle times are slower at getting patients out the door for a transfer.

I believe the original logic here is that door to puncture time includes tPA before the EVT so we need to remove that time to get time to EVT alone and the conservative estimate is to use the slower primary door to needle time. A simple alternative would be to subtract out the comprehensive door to needle time instead of the primary. Another option, perhaps closer to the original logic, would be to subtract out a generic primary DTN time rather than the specific one being used.

## Treatment of hemorrhagic strokes ##

Ayman's comment from the original model:

> Now we need the mRS breakdown for patients with hemorrhagic strokes.
        Currently making the conservative estimate that there is no
        difference in outcomes for ICH versus AIS patients, even though
        there is evidence to suggest to suggest ICH patients do almost
        about twice as well.
        This estimate also adjusts hemorrhagic stroke outcomes based on
        time to center.

If we continue to use AIS outcomes for ICH patients once we have hospital performance data we'll be incorporating door to needle and door to puncture times into ICH outcomes as well as time to center. If we have a way to estimate ICH outcomes directly from severity and/or time it would be a good idea to include it, and depending on the state of the literature and/or expert knowledge it may be better to use a fixed distribution. As it is we're essentially inflating the number of ischemic strokes (by a relatively small number) by treating all hemorrhagic strokes as if they were ischemic.

## Assumption of tPA ##

Should we model people who won't get tPA (and how)?

## What strategies should be included? ##

Before the recent refactoring, the Swift and python models included:

- a pure primary strategy for the closest primary center by travel time,
- a pure comprehensive strategy for the closest comprehensive center by travel time,
- a drip and ship strategy for every nearby primary center, with nearby defined heuristically via travel time and/or straight line distance. (Each primary center has a fixed transfer destination for the duration of a model run.)

The Swift model still uses this setup, while the vectorized python code now includes all "nearby" primary and comprehensive centers as pure strategies, and simply lets the model choose which is best. This eliminates many of the questions below, but they are still worth thinking about for the swift model and to be sure the python model makes sense.

In both versions, the total number of strategies depends on how many primary centers are nearby. Appropriately defining the "nearby" heuristic is mostly about computational time (and limiting mapping API calls) and depends on the task at hand, but is still pretty open. Updating to include individual hospital performance in the model introduces a couple new questions:

- Should transfer destinations account for hospital performance?
- Should "nearby" heuristics account for hospital performance to determine which drip and ship options to include?
- Should the definitions of closest primary and comprehensive center account for hospital performance? If yes:
    + Should this be based on the distribution itself or the random time used for each model run? (This interacts with the independence of estimated hospital times issue above.)
        * Currently in swift the closest is defined on each run and uses the random time.
    + How should this be done for comprehensive centers, where both door to needle and door to puncture impact outcomes?
    + Should we just let the model sort this out and include multiple pure primary and/or pure comprehensive strategies? This is the current choice of the python model, though it is made mostly to simplify vectorization.
