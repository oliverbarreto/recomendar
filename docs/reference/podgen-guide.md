---
title: "Installation — PodGen Documentation"
source: "https://podgen.readthedocs.io/en/latest/usage_guide/installation.html"
author:
published:
created: 2025-09-09
description:
tags:
  - "clippings"
---
PodGen can be used on any system (if not: file a bug report!), and officially supports Python 2.7 and 3.4, 3.5, 3.6 and 3.7.

Use [pip](https://pypi.python.org/pypi):

```default
$ pip install podgen
```

Remember to use a [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/)!

Note

One of the dependencies of PodGen, [lxml](https://lxml.de/), stopped supporting Python 3.4 in version 4.4.0. If you are installing PodGen using Python 3.4, you should select a compatible version of lxml by running e.g.:

```default
pip install 'lxml<4.4.0'
```

The step “Running setup.py install for lxml” will take several minutes and [requires installation of building tools](https://lxml.de/installation.html), since the lxml version does not include pre-built binaries.

---

---
title: "Podcasts — PodGen Documentation"
source: "https://podgen.readthedocs.io/en/latest/usage_guide/podcasts.html"
author:
published:
created: 2025-09-09
description:
tags:
  - "clippings"
---
In PodGen, the term *podcast* refers to the show which listeners can subscribe to, which consists of individual *episodes*. Therefore, the Podcast class will be the first thing you start with.

## Creating a new instance¶

You can start with a blank podcast by invoking the Podcast constructor with no arguments, like this:

```default
from podgen import Podcast
p = Podcast()
```

## Mandatory attributes¶

There are four attributes which must be set before you can generate your podcast. They are mandatory because Apple’s podcast directory will not accept podcasts without this information. If you try to generate the podcast without setting all of the mandatory attributes, you will get an error.

The mandatory attributes are:

```default
p.name = "My Example Podcast"
p.description = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
p.website = "https://example.org"
p.explicit = False
```

They’re mostly self explanatory, but you can read more about them if you’d like:

- [`name`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.name "podgen.Podcast.name")
- [`description`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.description "podgen.Podcast.description")
- [`website`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.website "podgen.Podcast.website")
- [`explicit`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.explicit "podgen.Podcast.explicit")

## Image¶

A podcast’s image is worth special attention:

```default
p.image = "https://example.com/static/example_podcast.png"
```

`Podcast.``image`

The URL of the artwork for this podcast. iTunes prefers square images that are at least `1400x1400` pixels. Podcasts with an image smaller than this are *not* eligible to be featured on the iTunes Store.

iTunes supports images in JPEG and PNG formats with an RGB color space (CMYK is not supported). The URL must end in “.jpg” or “.png”; if they don’t, a [`NotSupportedByItunesWarning`](https://podgen.readthedocs.io/en/latest/api.warnings.html#podgen.warnings.NotSupportedByItunesWarning "podgen.warnings.NotSupportedByItunesWarning") will be issued.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| ----- | ------------------------------------------------------------------------------- |
| RSS:  | itunes:image                                                                    |

Note

If you change your podcast’s image, you must also change the file’s name; iTunes doesn’t check the image to see if it has changed.

Additionally, the server hosting your cover art image must allow HTTP HEAD requests (most servers support this).

Even though the image *technically* is optional, you won’t reach people without it.

## Optional attributes¶

There are plenty of other attributes that can be used with [`podgen.Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast"):

### Commonly used¶

```default
p.copyright = "2016 Example Radio"
p.language = "en-US"
p.authors = [Person("John Doe", "editor@example.org")]
p.feed_url = "https://example.com/feeds/podcast.rss"  # URL of this feed
p.category = Category("Music", "Music History")
p.owner = p.authors[0]
p.xslt = "https://example.com/feed/stylesheet.xsl"  # URL of XSLT stylesheet
```

Read more:

- [`copyright`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.copyright "podgen.Podcast.copyright")
- [`language`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.language "podgen.Podcast.language")
- [`authors`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.authors "podgen.Podcast.authors")
- [`feed_url`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.feed_url "podgen.Podcast.feed_url")
- [`category`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.category "podgen.Podcast.category")
- [`owner`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.owner "podgen.Podcast.owner")
- [`xslt`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.xslt "podgen.Podcast.xslt")

### Less commonly used¶

Some of those are obscure while some of them are often times not needed. Others again have very reasonable defaults.

```default
# RSS Cloud enables podcatchers to subscribe to notifications when there's
# a new episode ready, however it's not used much.
p.cloud = ("server.example.com", 80, "/rpc", "cloud.notify", "xml-rpc")

import datetime
# pytz is a dependency of this library, and makes it easy to deal with
# timezones. Generally, all dates must be timezone aware.
import pytz
# last_updated is datetime when the feed was last refreshed. If you don't
# set it, the current date and time will be used instead when the feed is
# generated, which is generally what you want. Nevertheless, you can
# set your own date:
p.last_updated = datetime.datetime(2016, 5, 18, 0, 0, tzinfo=pytz.utc))

# publication_date is when the contents of this feed last were published.
# If you don't set it, the date of the most recent Episode is used. Again,
# this is generally what you want, but you can override it:
p.publication_date = datetime.datetime(2016, 5, 17, 15, 32,tzinfo=pytz.utc))

# Set of days on which podcatchers won't need to refresh the feed.
# Not implemented widely.
p.skip_days = {"Friday", "Saturday", "Sunday"}

# Set of hours on which podcatchers won't need to refresh the feed.
# Not implemented widely.
p.skip_hours = set(range(8))
p.skip_hours |= set(range(16, 24))

# Person to contact regarding technical aspects of the feed.
p.web_master = Person(None, "helpdesk@dallas.example.com")

# Identify the software which generates the feed (defaults to python-podgen)
p.set_generator("ExamplePodcastProgram", (1,0,0))
# (you can also set the generator string directly)
p.generator = "ExamplePodcastProgram v1.0.0 (with help from python-feedgen)"

# !!! Be very careful about using the following attributes !!!

# Tell iTunes that this feed has moved somewhere else.
p.new_feed_url = "https://podcast.example.com/example"

# Tell iTunes that this feed will never be updated again.
p.complete = True

# Tell iTunes that you'd rather not have this feed appear on iTunes.
p.withhold_from_itunes = True
```

Read more:

- [`cloud`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.cloud "podgen.Podcast.cloud")
- [`last_updated`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.last_updated "podgen.Podcast.last_updated")
- [`publication_date`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.publication_date "podgen.Podcast.publication_date")
- [`skip_days`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.skip_days "podgen.Podcast.skip_days")
- [`skip_hours`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.skip_hours "podgen.Podcast.skip_hours")
- [`web_master`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.web_master "podgen.Podcast.web_master")
- [`set_generator()`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.set_generator "podgen.Podcast.set_generator")
- [`new_feed_url`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.new_feed_url "podgen.Podcast.new_feed_url")
- [`complete`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.complete "podgen.Podcast.complete")
- [`withhold_from_itunes`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.withhold_from_itunes "podgen.Podcast.withhold_from_itunes")

## Shortcut for filling in data¶

Instead of creating a new [`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast") object in one statement, and populating it with data one statement at a time afterwards, you can create a new [`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast") object and fill it with data in one statement. Simply use the attribute name as keyword arguments to the constructor:

```default
import podgen
p = podgen.Podcast(
    <attribute name>=<attribute value>,
    <attribute name>=<attribute value>,
    ...
)
```

Using this technique, you can define the Podcast as part of a list comprehension, dictionaries and so on. Take a look at the [API Documentation for Podcast](https://podgen.readthedocs.io/en/latest/api.podcast.html) for a practical example.


---

---
title: "Episodes — PodGen Documentation"
source: "https://podgen.readthedocs.io/en/latest/usage_guide/episodes.html"
author:
published:
created: 2025-09-09
description:
tags:
  - "clippings"
---
Once you have created and populated a Podcast, you probably want to add some episodes to it. To add episodes to a feed, you need to create new [`podgen.Episode`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode "podgen.Episode") objects and append them to the list of episodes in the Podcast. That is pretty straight-forward:

```default
from podgen import Podcast, Episode
# Create the podcast (see the previous section)
p = Podcast()
# Create new episode
my_episode = Episode()
# Add it to the podcast
p.episodes.append(my_episode)
```

There is a convenience method called [`Podcast.add_episode`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.add_episode "podgen.Podcast.add_episode") which optionally creates a new instance of [`Episode`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode "podgen.Episode"), adds it to the podcast and returns it, allowing you to assign it to a variable:

```default
from podgen import Podcast
p = Podcast()
my_episode = p.add_episode()
```

If you prefer to use the constructor, there’s nothing wrong with that:

```default
from podgen import Podcast, Episode
p = Podcast()
my_episode = p.add_episode(Episode())
```

The advantage of using the latter form is that you can pass data to the constructor.

## Filling with data¶

There is only one rule for episodes: **they must have either a title or a summary**, or both. Additionally, you can opt to have a long summary, as well as a short subtitle:

```default
my_episode.title = "S01E10: The Best Example of them All"
my_episode.subtitle = "We found the greatest example!"
my_episode.summary = "In this week's episode, we have found the " + \
                     "<i>greatest</i> example of them all."
my_episode.long_summary = "In this week's episode, we went out on a " + \
    "search to find the <i>greatest</i> example of them " + \
    "all. <br/>Today's intro music: " + \
    "<a href='https://www.youtube.com/watch?v=dQw4w9WgXcQ'>Example Song</a>"
```

Read more:

- [`title`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.title "podgen.Episode.title")
- [`subtitle`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.subtitle "podgen.Episode.subtitle")
- [`summary`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.summary "podgen.Episode.summary")
- [`long_summary`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.long_summary "podgen.Episode.long_summary")

### Enclosing media¶

Of course, this isn’t much of a podcast if we don’t have any [`media`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.media "podgen.Episode.media") attached to it!

```default
from datetime import timedelta
from podgen import Media
my_episode.media = Media("http://example.com/podcast/s01e10.mp3",
                         size=17475653,
                         type="audio/mpeg",  # Optional, can be determined
                                             # from the url
                         duration=timedelta(hours=1, minutes=2, seconds=36)
                        )
```

The media’s attributes (and the arguments to the constructor) are:

| Attribute                                                                                                          | Description                                                                                                                                                                                                                                      |
| ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`url`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.url "podgen.Media.url")                | The URL at which this media file is accessible.                                                                                                                                                                                                  |
| [`size`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.size "podgen.Media.size")             | The size of the media file as bytes, given either as [`int`](https://docs.python.org/3/library/functions.html#int "(in Python v3.8)") or a [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") which will be parsed. |
| [`type`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.type "podgen.Media.type")             | The media file’s [MIME type](https://en.wikipedia.org/wiki/Media_type).                                                                                                                                                                          |
| [`duration`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.duration "podgen.Media.duration") | How long the media file lasts, given as a [`datetime.timedelta`](https://docs.python.org/3/library/datetime.html#datetime.timedelta "(in Python v3.8)")                                                                                          |

You can leave out some of these:

| Attribute                                                                                                          | Effect if left out                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| [`url`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.url "podgen.Media.url")                | Mandatory.                                                                                                                                |
| [`size`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.size "podgen.Media.size")             | Can be 0, but do so only if you cannot determine its size (for example if it’s a stream).                                                 |
| [`type`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.type "podgen.Media.type")             | Can be left out if the URL has a recognized file extensions. In that case, the type will be determined from the URL’s file extension.     |
| [`duration`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.duration "podgen.Media.duration") | Can be left out since it is optional. It will stay as [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)"). |

Warning

Remember to encode special characters in your URLs! For example, say you have a file named `library-pod-#023-future.mp3`, which you host at `http://podcast.example.org/episodes`. You might try to use the URL `http://podcast.example.org/episodes/library-pod-#023-future.mp3`. This, however, will not work, since the hash (#) has a special meaning in URLs. Instead, you should use [`urllib.parse.quote()`](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.quote "(in Python v3.8)") in Python3, or `urllib.quote()` in Python2, to escape the special characters in the filename in the URL. The correct URL would then become `http://podcast.example.org/episodes/library-pod-%23023-future.mp3`.

#### Populating size and type from server¶

By using the special factory [`Media.create_from_server_response`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.create_from_server_response "podgen.Media.create_from_server_response") you can gather missing information by asking the server at which the file is hosted:

```default
my_episode.media = Media.create_from_server_response(
                       "http://example.com/podcast/s01e10.mp3",
                       duration=timedelta(hours=1, minutes=2, seconds=36)
                   )
```

Here’s the effect of leaving out the fields:

| Attribute                                                                                                          | Effect if left out                                                                                                                             |
| ------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| [`url`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.url "podgen.Media.url")                | Mandatory.                                                                                                                                     |
| [`size`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.size "podgen.Media.size")             | Will be populated using the `Content-Length` header.                                                                                           |
| [`type`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.type "podgen.Media.type")             | Will be populated using the `Content-Type` header.                                                                                             |
| [`duration`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.duration "podgen.Media.duration") | Will *not* be populated by data from the server; will stay [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)"). |

#### Populating duration from server¶

Determining duration requires that the media file is downloaded to the local machine, and is therefore not done unless you specifically ask for it. If you don’t have the media file locally, you can populate the [`duration`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.duration "podgen.Media.duration") field by using [`Media.fetch_duration()`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.fetch_duration "podgen.Media.fetch_duration"):

```default
my_episode.media.fetch_duration()
```

If you *do* happen to have the media file in your file system, you can use it to populate the [`duration`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.duration "podgen.Media.duration") attribute by calling [`Media.populate_duration_from()`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.populate_duration_from "podgen.Media.populate_duration_from"):

```default
filename = "/home/example/Music/podcast/s01e10.mp3"
my_episode.media.populate_duration_from(filename)
```

Note

Even though you technically can have file names which don’t end in their actual file extension, iTunes will use the file extension to determine what type of file it is, without even asking the server. You must therefore make sure your media files have the correct file extension.

If you don’t care about compatibility with iTunes, you can provide the MIME type yourself to fix any errors you receive about this.

This also applies to the tool used to determine a file’s duration, which uses the file’s file extension to determine its type.

Read more about:

- [`podgen.Episode.media`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.media "podgen.Episode.media") (the attribute)
- [`podgen.Media`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media "podgen.Media") (the class which you use as value)

### Identifying the episode¶

Every episode is identified by a **globally unique identifier (GUID)**. By default, this id is set to be the same as the URL of the media (see above) when the feed is generated. That is, given the example above, the id of `my_episode` would be `http://example.com/podcast/s01e10.mp3`.

Warning

An episode’s ID should never change. Therefore, **if you don’t set id, the media URL must never change either**.

Read more about [`the id attribute`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.id "podgen.Episode.id").

### Episode’s publication date¶

An episode’s publication date indicates when the episode first went live. It is used to indicate how old the episode is, and a client may say an episode is from “1 hour ago”, “yesterday”, “last week” and so on. You should therefore make sure that it matches the exact time that the episode went live, or else your listeners will get a new episode which appears to have existed for longer than it has.

Note

It is generally a bad idea to use the media file’s modification date as the publication date. If you make your episodes some time in advance, your listeners will suddenly get an “old” episode in their feed!

```default
my_episode.publication_date = datetime.datetime(2016, 5, 18, 10, 0,
                                              tzinfo=pytz.utc)
```

Read more about [`the publication_date attribute`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.publication_date "podgen.Episode.publication_date").

### The Link¶

If you’re publishing articles along with your podcast episodes, you should link to the relevant article. Examples can be linking to the sound on SoundCloud or the post on your website. Usually, your listeners expect to find the entirety of the [`summary`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.summary "podgen.Episode.summary") by following the link.

```default
my_episode.link = "http://example.com/article/2016/05/18/Best-example"
```

Note

If you don’t have anything to link to, then that’s fine as well. No link is better than a disappointing link.

Read more about [`the link attribute`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.link "podgen.Episode.link").

### Less used attributes¶

```default
# Not actually implemented by iTunes; the Podcast's image is used.
my_episode.image = "http://example.com/static/best-example.png"

# Set it to override the Podcast's explicit attribute for this episode only.
my_episode.explicit = False

# Tell iTunes that the enclosed video is closed captioned.
my_episode.is_closed_captioned = False

# Tell iTunes that this episode should be the first episode on the store
# page.
my_episode.position = 1

# Careful! This will hide this episode from the iTunes store page.
my_episode.withhold_from_itunes = True
```

More details:

- [`image`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.image "podgen.Episode.image")
- [`explicit`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.explicit "podgen.Episode.explicit")
- [`is_closed_captioned`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.is_closed_captioned "podgen.Episode.is_closed_captioned")
- [`position`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.position "podgen.Episode.position")
- [`withhold_from_itunes`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.withhold_from_itunes "podgen.Episode.withhold_from_itunes")

## Shortcut for filling in data¶

Instead of assigning those values one at a time, you can assign them all in one go in the constructor – just like you can with Podcast. Just use the attribute name as the keyword:

```default
Episode(
    <attribute name>=<attribute value>,
    <attribute name>=<attribute value>,
    ...
)
```

See also the example in [the API Documentation](https://podgen.readthedocs.io/en/latest/api.episode.html).


---

---
title: "RSS — PodGen Documentation"
source: "https://podgen.readthedocs.io/en/latest/usage_guide/rss.html"
author:
published:
created: 2025-09-09
description:
tags:
  - "clippings"
---
Once you’ve added all the information and episodes, you’re ready to take the final step:

```default
rssfeed = p.rss_str()
# Print to stdout, just as an example
print(rssfeed)
```

If you’re okay with the default parameters of [`podgen.Podcast.rss_str()`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.rss_str "podgen.Podcast.rss_str"), you can use a shortcut by converting your [`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast") to [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)"):

```default
rssfeed = str(p)
print(rssfeed)
# Or let print convert to str for you
print(p)
```

| [`rss_str`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.rss_str "podgen.Podcast.rss_str")(\[minimize, encoding, xml\_declaration\]) | Generate an RSS feed and return the feed XML as string. |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |

You may also write the feed to a file directly, using [`podgen.Podcast.rss_file()`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.rss_file "podgen.Podcast.rss_file"):

```default
p.rss_file('rss.xml', minimize=True)
```

| [`rss_file`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.rss_file "podgen.Podcast.rss_file")(filename\[, minimize, encoding, …\]) | Generate an RSS feed and write the resulting XML to a file. |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |

Note

If there are any mandatory attributes that aren’t set, you’ll get errors when generating the RSS.

Note

Generating the RSS is not completely free. Save the result to a variable once instead of generating the same RSS over and over.


---

---
title: "Full example — PodGen Documentation"
source: "https://podgen.readthedocs.io/en/latest/usage_guide/example.html"
author:
published:
created: 2025-09-09
description:
tags:
  - "clippings"
---
This example is located at `podgen/__main__.py` in the package, and is run as part of the [testing routines](https://podgen.readthedocs.io/en/latest/contributing.html).

| ```  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 ``` | ``` def main():     """Create an example podcast and print it or save it to a file."""     # There must be exactly one argument, and it is must end with rss     if len(sys.argv) != 2 or not (             sys.argv[1].endswith('rss')):         # Invalid usage, print help message         # print_enc is just a custom function which functions like print,         # except it deals with byte arrays properly.         print_enc ('Usage: %s ( <file>.rss \| rss )' % \                 'python -m podgen')         print_enc ('')         print_enc ('  rss              -- Generate RSS test output and print it to stdout.')         print_enc ('  <file>.rss       -- Generate RSS test teed and write it to file.rss.')         print_enc ('')         exit()      # Remember what type of feed the user wants     arg = sys.argv[1]      from podgen import Podcast, Person, Media, Category, htmlencode     # Initialize the feed     p = Podcast()     p.name = 'Testfeed'     p.authors.append(Person("Lars Kiesow", "lkiesow@uos.de"))     p.website = 'http://example.com'     p.copyright = 'cc-by'     p.description = 'This is a cool feed!'     p.language = 'de'     p.feed_url = 'http://example.com/feeds/myfeed.rss'     p.category = Category('Leisure', 'Aviation')     p.explicit = False     p.complete = False     p.new_feed_url = 'http://example.com/new-feed.rss'     p.owner = Person('John Doe', 'john@example.com')     p.xslt = "http://example.com/stylesheet.xsl"      e1 = p.add_episode()     e1.id = 'http://lernfunk.de/_MEDIAID_123#1'     e1.title = 'First Element'     e1.summary = htmlencode('''Lorem ipsum dolor sit amet, consectetur adipiscing elit. Tamen             aberramus a proposito, et, ne longius, prorsus, inquam, Piso, si ista             mala sunt, placet. Aut etiam, ut vestitum, sic sententiam habeas aliam             domesticam, aliam forensem, ut in fronte ostentatio sit, intus veritas             occultetur? Cum id fugiunt, re eadem defendunt, quae Peripatetici,             verba <3.''')     e1.link = 'http://example.com'     e1.authors = [Person('Lars Kiesow', 'lkiesow@uos.de')]     e1.publication_date = datetime.datetime(2014, 5, 17, 13, 37, 10, tzinfo=pytz.utc)     e1.media = Media("http://example.com/episodes/loremipsum.mp3", 454599964,                      duration=                      datetime.timedelta(hours=1, minutes=32, seconds=19))      # Should we just print out, or write to file?     if arg == 'rss':         # Print         print_enc(p.rss_str())     elif arg.endswith('rss'):         # Write to file         p.rss_file(arg, minimize=True) ``` |

---
