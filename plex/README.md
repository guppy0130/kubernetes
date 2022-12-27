# plex

## Shortcomings

* Have to claim with `overlays/location/deployment-preferences.xml`
* Non-mountable configmap for `Preferences.xml` (because app should write to it)
* Can't use new movie/tv library agents for some reason

```log
2022-11-27 22:43:31,803 (7f6babfb5b38) :  ERROR (networking:196) - Error opening URL 'http://127.0.0.1:32400/:/plugins/com.plexapp.agents.thetvdb'
2022-11-27 22:43:31,811 (7f6babfb5b38) :  WARNING (agentservice:169) - We weren't able to get information from the server about the agents.
```
