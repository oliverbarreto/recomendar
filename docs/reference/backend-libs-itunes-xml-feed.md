# iTunes XML Feed
- https://podgen.readthedocs.io/en/latest/
- https://github.com/tobinus/python-podgen/tree/master
  
This library allows creating podcast RSS/XML feeds compatible with iTunes. This is a clean and simple library which helps you generate podcast RSS feeds from your Python code? Here is how you do that with PodGen:

```python
from podgen import Podcast, Episode, Media
# Create the Podcast
p = Podcast(
   name="Animals Alphabetically",
   description="Every Tuesday, biologist John Doe and wildlife "
               "photographer Foo Bar introduce you to a new animal.",
   website="http://example.org/animals-alphabetically",
   explicit=False,
)
# Add some episodes
p.episodes += [
   Episode(
     title="Aardvark",
     media=Media("http://example.org/files/aardvark.mp3", 11932295),
     summary="With an English name adapted directly from Afrikaans "
             '-- literally meaning "earth pig" -- this fascinating '
             "animal has both circular teeth and a knack for "
             "digging.",
   ),
   Episode(
      title="Alpaca",
      media=Media("http://example.org/files/alpaca.mp3", 15363464),
      summary="Thousands of years ago, alpacas were already "
              "domesticated and bred to produce the best fibers. "
              "Case in point: we have found clothing made from "
              "alpaca fiber that is 2000 years old. How is this "
              "possible, and what makes it different from llamas?",
   ),
]
# Generate the RSS feed
rss = p.rss_str()
```

You don’t need to read the RSS specification, write XML by hand or wrap your head around ambiguous, undocumented APIs. PodGen incorporates the industry’s best practices and lets you focus on collecting the necessary metadata and publishing the podcast.

PodGen is compatible with Python 2.7 and 3.4+.

Warning
As of March 6th 2020 (v1.1.0), PodGen does not support the additions and changes made by Apple to their podcast standards since 2016, with the exception of the 2019 categories. This includes the ability to mark episodes with episode and season number, and the ability to mark the podcast as “serial”. It is a goal to implement those changes in a new release. Please refer to the Roadmap.


## Installation


PodGen can be used on any system (if not: file a bug report!), and officially supports Python 2.7 and 3.4, 3.5, 3.6 and 3.7.

Use [pip](https://pypi.python.org/pypi):

```
$ pip install podgen
```

Remember to use a [virtual environment](http://docs.python-guide.org/en/latest/dev/virtualenvs/)!

Note

One of the dependencies of PodGen, [lxml](https://lxml.de/), stopped supporting Python 3.4 in version 4.4.0. If you are installing PodGen using Python 3.4, you should select a compatible version of lxml by running e.g.:

```
pip install 'lxml<4.4.0'
```

The step “Running setup.py install for lxml” will take several minutes and[requires installation of building tools](https://lxml.de/installation.html), since the lxml version does not include pre-built binaries.


## Podcasts

In PodGen, the term *podcast* refers to the show which listeners can subscribe to, which consists of individual *episodes*. Therefore, the Podcast class will be the first thing you start with.

## Creating a new instance

You can start with a blank podcast by invoking the Podcast constructor with no arguments, like this:

```
from podgen import Podcast
p = Podcast()
```

## Mandatory attributes

There are four attributes which must be set before you can generate your podcast. They are mandatory because Apple’s podcast directory will not accept podcasts without this information. If you try to generate the podcast without setting all of the mandatory attributes, you will get an error.

The mandatory attributes are:

```
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

## Image

A podcast’s image is worth special attention:

```
p.image = "https://example.com/static/example_podcast.png"
```

`Podcast.``image`

The URL of the artwork for this podcast. iTunes prefers square images that are at least `1400x1400` pixels. Podcasts with an image smaller than this are *not* eligible to be featured on the iTunes Store.

iTunes supports images in JPEG and PNG formats with an RGB color space (CMYK is not supported). The URL must end in “.jpg” or “.png”; if they don’t, a [`NotSupportedByItunesWarning`](https://podgen.readthedocs.io/en/latest/api.warnings.html#podgen.warnings.NotSupportedByItunesWarning "podgen.warnings.NotSupportedByItunesWarning") will be issued.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | itunes:image |

Note

If you change your podcast’s image, you must also change the file’s name; iTunes doesn’t check the image to see if it has changed.

Additionally, the server hosting your cover art image must allow HTTP HEAD requests (most servers support this).

Even though the image *technically* is optional, you won’t reach people without it.

## Optional attributes

There are plenty of other attributes that can be used with[`podgen.Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast"):

### Commonly used

```
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
- [`feed_url`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.feed_url "podgen.Podcast.feed_url")
- [`category`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.category "podgen.Podcast.category")
- [`owner`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.owner "podgen.Podcast.owner")
- [`xslt`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.xslt "podgen.Podcast.xslt")

### Less commonly used

Some of those are obscure while some of them are often times not needed. Others again have very reasonable defaults.

```
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

## Shortcut for filling in data

Instead of creating a new [`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast") object in one statement, and populating it with data one statement at a time afterwards, you can create a new [`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast") object and fill it with data in one statement. Simply use the attribute name as keyword arguments to the constructor:

```
import podgen
p = podgen.Podcast(
    <attribute name>=<attribute value>,
    <attribute name>=<attribute value>,
    ...
)
```

Using this technique, you can define the Podcast as part of a list comprehension, dictionaries and so on. Take a look at the [API Documentation for Podcast](https://podgen.readthedocs.io/en/latest/api.podcast.html) for a practical example.


## Episodes

Once you have created and populated a Podcast, you probably want to add some episodes to it. To add episodes to a feed, you need to create new [`podgen.Episode`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode "podgen.Episode") objects and append them to the list of episodes in the Podcast. That is pretty straight-forward:

```
from podgen import Podcast, Episode
# Create the podcast (see the previous section)
p = Podcast()
# Create new episode
my_episode = Episode()
# Add it to the podcast
p.episodes.append(my_episode)
```

There is a convenience method called [`Podcast.add_episode`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.add_episode "podgen.Podcast.add_episode")which optionally creates a new instance of [`Episode`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode "podgen.Episode"), adds it to the podcast and returns it, allowing you to assign it to a variable:

```
from podgen import Podcast
p = Podcast()
my_episode = p.add_episode()
```

If you prefer to use the constructor, there’s nothing wrong with that:

```
from podgen import Podcast, Episode
p = Podcast()
my_episode = p.add_episode(Episode())
```

The advantage of using the latter form is that you can pass data to the constructor.

## Filling with data

There is only one rule for episodes: **they must have either a title or a summary**, or both. Additionally, you can opt to have a long summary, as well as a short subtitle:

```
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

### Enclosing media

Of course, this isn’t much of a podcast if we don’t have any[`media`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.media "podgen.Episode.media") attached to it!

```
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

| Attribute | Description |
| --- | --- |
| [`url`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.url "podgen.Media.url") | The URL at which this media file is accessible. |
| [`size`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.size "podgen.Media.size") | The size of the media file as bytes, given either as [`int`](https://docs.python.org/3/library/functions.html#int "(in Python v3.8)") or a [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") which will be parsed. |
| [`type`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.type "podgen.Media.type") | The media file’s [MIME type](https://en.wikipedia.org/wiki/Media_type). |
| [`duration`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.duration "podgen.Media.duration") | How long the media file lasts, given as a [`datetime.timedelta`](https://docs.python.org/3/library/datetime.html#datetime.timedelta "(in Python v3.8)") |

You can leave out some of these:

| Attribute | Effect if left out |
| --- | --- |
| [`url`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.url "podgen.Media.url") | Mandatory. |
| [`size`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.size "podgen.Media.size") | Can be 0, but do so only if you cannot determine its size (for example if it’s a stream). |
| [`type`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.type "podgen.Media.type") | Can be left out if the URL has a recognized file extensions. In that case, the type will be determined from the URL’s file extension. |
| [`duration`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.duration "podgen.Media.duration") | Can be left out since it is optional. It will stay as [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)"). |

Warning

Remember to encode special characters in your URLs! For example, say you have a file named `library-pod-#023-future.mp3`, which you host at`http://podcast.example.org/episodes`. You might try to use the URL`http://podcast.example.org/episodes/library-pod-#023-future.mp3`. This, however, will not work, since the hash (#) has a special meaning in URLs. Instead, you should use [`urllib.parse.quote()`](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.quote "(in Python v3.8)") in Python3, or`urllib.quote()` in Python2, to escape the special characters in the filename in the URL. The correct URL would then become`http://podcast.example.org/episodes/library-pod-%23023-future.mp3`.

#### Populating size and type from server

By using the special factory[`Media.create_from_server_response`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.create_from_server_response "podgen.Media.create_from_server_response")you can gather missing information by asking the server at which the file is hosted:

```
my_episode.media = Media.create_from_server_response(
                       "http://example.com/podcast/s01e10.mp3",
                       duration=timedelta(hours=1, minutes=2, seconds=36)
                   )
```

Here’s the effect of leaving out the fields:

| Attribute | Effect if left out |
| --- | --- |
| [`url`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.url "podgen.Media.url") | Mandatory. |
| [`size`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.size "podgen.Media.size") | Will be populated using the `Content-Length` header. |
| [`type`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.type "podgen.Media.type") | Will be populated using the `Content-Type` header. |
| [`duration`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.duration "podgen.Media.duration") | Will *not* be populated by data from the server; will stay [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)"). |

#### Populating duration from server

Determining duration requires that the media file is downloaded to the local machine, and is therefore not done unless you specifically ask for it. If you don’t have the media file locally, you can populate the [`duration`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.duration "podgen.Media.duration")field by using [`Media.fetch_duration()`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.fetch_duration "podgen.Media.fetch_duration"):

```
my_episode.media.fetch_duration()
```

If you *do* happen to have the media file in your file system, you can use it to populate the [`duration`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.duration "podgen.Media.duration") attribute by calling[`Media.populate_duration_from()`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media.populate_duration_from "podgen.Media.populate_duration_from"):

```
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

### Identifying the episode

Every episode is identified by a **globally unique identifier (GUID)**. By default, this id is set to be the same as the URL of the media (see above) when the feed is generated. That is, given the example above, the id of `my_episode` would be`http://example.com/podcast/s01e10.mp3`.

Warning

An episode’s ID should never change. Therefore, **if you don’t set id, the media URL must never change either**.

Read more about [`the id attribute`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.id "podgen.Episode.id").

### The Link

If you’re publishing articles along with your podcast episodes, you should link to the relevant article. Examples can be linking to the sound on SoundCloud or the post on your website. Usually, your listeners expect to find the entirety of the [`summary`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.summary "podgen.Episode.summary") by following the link.

```
my_episode.link = "http://example.com/article/2016/05/18/Best-example"
```

Note

If you don’t have anything to link to, then that’s fine as well. No link is better than a disappointing link.

Read more about [`the link attribute`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.link "podgen.Episode.link").

### The Authors

Normally, the attributes and [`Podcast.web_master`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.web_master "podgen.Podcast.web_master") (if set) are used to determine the authors of an episode. Thus, if all your episodes have the same authors, you should just set it at the podcast level.

If an episode’s list of authors differs from the podcast’s, though, you can override it like this:

```
my_episode.authors = [Person("Joe Bob")]
```

You can even have multiple authors:

```
my_episode.authors = [Person("Joe Bob"), Person("Alice Bob")]
```

Read more about .

### Less used attributes

```
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

## Shortcut for filling in data

Instead of assigning those values one at a time, you can assign them all in one go in the constructor – just like you can with Podcast. Just use the attribute name as the keyword:

```
Episode(
    <attribute name>=<attribute value>,
    <attribute name>=<attribute value>,
    ...
)
```

See also the example in [the API Documentation](https://podgen.readthedocs.io/en/latest/api.episode.html).


## RSS

Once you’ve added all the information and episodes, you’re ready to take the final step:

```
rssfeed = p.rss_str()
# Print to stdout, just as an example
print(rssfeed)
```

If you’re okay with the default parameters of [`podgen.Podcast.rss_str()`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.rss_str "podgen.Podcast.rss_str"), you can use a shortcut by converting your [`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast") to [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)"):

```
rssfeed = str(p)
print(rssfeed)
# Or let print convert to str for you
print(p)
```

| [`rss_str`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.rss_str "podgen.Podcast.rss_str") (\[minimize, encoding, xml\_declaration\]) | Generate an RSS feed and return the feed XML as string. |
| --- | --- |

You may also write the feed to a file directly, using [`podgen.Podcast.rss_file()`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.rss_file "podgen.Podcast.rss_file"):

```
p.rss_file('rss.xml', minimize=True)
```

| [`rss_file`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.rss_file "podgen.Podcast.rss_file") (filename\[, minimize, encoding, …\]) | Generate an RSS feed and write the resulting XML to a file. |
| --- | --- |

Note

If there are any mandatory attributes that aren’t set, you’ll get errors when generating the RSS.

Note

Generating the RSS is not completely free. Save the result to a variable once instead of generating the same RSS over and over.


## Full Example

```python
# Full example
# This example is located at podgen/__main__.py in the package, and is run as part of the testing routines.
def main():
    """Create an example podcast and print it or save it to a file."""
    # There must be exactly one argument, and it is must end with rss
    if len(sys.argv) != 2 or not (
            sys.argv[1].endswith('rss')):
        # Invalid usage, print help message
        # print_enc is just a custom function which functions like print,
        # except it deals with byte arrays properly.
        print_enc ('Usage: %s ( <file>.rss | rss )' % \
                'python -m podgen')
        print_enc ('')
        print_enc ('  rss              -- Generate RSS test output and print it to stdout.')
        print_enc ('  <file>.rss       -- Generate RSS test teed and write it to file.rss.')
        print_enc ('')
        exit()

    # Remember what type of feed the user wants
    arg = sys.argv[1]

    from podgen import Podcast, Person, Media, Category, htmlencode
    # Initialize the feed
    p = Podcast()
    p.name = 'Testfeed'
    p.authors.append(Person("Lars Kiesow", "lkiesow@uos.de"))
    p.website = 'http://example.com'
    p.copyright = 'cc-by'
    p.description = 'This is a cool feed!'
    p.language = 'de'
    p.feed_url = 'http://example.com/feeds/myfeed.rss'
    p.category = Category('Leisure', 'Aviation')
    p.explicit = False
    p.complete = False
    p.new_feed_url = 'http://example.com/new-feed.rss'
    p.owner = Person('John Doe', 'john@example.com')
    p.xslt = "http://example.com/stylesheet.xsl"

    e1 = p.add_episode()
    e1.id = 'http://lernfunk.de/_MEDIAID_123#1'
    e1.title = 'First Element'
    e1.summary = htmlencode('''Lorem ipsum dolor sit amet, consectetur adipiscing elit. Tamen
            aberramus a proposito, et, ne longius, prorsus, inquam, Piso, si ista
            mala sunt, placet. Aut etiam, ut vestitum, sic sententiam habeas aliam
            domesticam, aliam forensem, ut in fronte ostentatio sit, intus veritas
            occultetur? Cum id fugiunt, re eadem defendunt, quae Peripatetici,
            verba <3.''')
    e1.link = 'http://example.com'
    e1.authors = [Person('Lars Kiesow', 'lkiesow@uos.de')]
    e1.publication_date = datetime.datetime(2014, 5, 17, 13, 37, 10, tzinfo=pytz.utc)
    e1.media = Media("http://example.com/episodes/loremipsum.mp3", 454599964,
                     duration=
                     datetime.timedelta(hours=1, minutes=32, seconds=19))

    # Should we just print out, or write to file?
    if arg == 'rss':
        # Print
        print_enc(p.rss_str())
    elif arg.endswith('rss'):
        # Write to file
        p.rss_file(arg, minimize=True)
```


## Adding new tags

Are there XML elements you want to use that aren’t supported by PodGen? If so, you should be able to add them in using inheritance.

Note

There hasn’t been a focus on making it easy to extend PodGen. Future versions may provide better support for this.

Note

Feel free to add a feature request to [GitHub Issues](https://github.com/tobinus/python-podgen/issues) if you think PodGen should support a certain element out of the box.

## Quick How-to

1. Create new class that extends [`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast").
2. Add the new attribute.
3. Override `_create_rss()`, call `super()._create_rss()`, add the new element to its result and return the new tree.

You can do the same with [`Episode`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode "podgen.Episode"), if you replace`_create_rss()` with `rss_entry()` above.

There are plenty of small quirks you have to keep in mind. You are strongly encouraged to read the example below.

### Using namespaces

If you’ll use RSS elements from another namespace, you must make sure you update the `_nsmap` attribute of [`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast")(you cannot define new namespaces from an episode!). It is a dictionary with the prefix as key and the URI for that namespace as value. To use a namespace, you must put the URI inside curly braces, with the tag name following right after (outside the braces). For example:

```
"{%s}link" % self._nsmap['atom']  # This will render as atom:link
```

The [lxml API documentation](http://lxml.de/api/index.html) is a pain to read, so just look at the [source code for PodGen](https://github.com/tobinus/python-podgen/blob/master/podgen/podcast.py) and the example below.

## Example: Adding a ttl element

The examples here assume version 3 of Python is used.

`ttl` is an RSS element and stands for “time to live”, and can only be an integer which indicates how many minutes the podcatcher can rely on its copy of the feed before refreshing (or something like that). There is confusion as to what it is supposed to mean (max refresh frequency? min refresh frequency?), which is why it is not included in PodGen. If you use it, you should treat it as the **recommended** update period (source: [RSS Best Practices](http://www.rssboard.org/rss-profile#element-channel-ttl)).

### Using traditional inheritance

```
# The module used to create the XML tree and generate the XML
from lxml import etree

# The class we will extend
from podgen import Podcast

class PodcastWithTtl(Podcast):
    """This is an extension of Podcast, which supports ttl.

    You gain access to ttl by creating a new instance of this class instead
    of Podcast.
    """
    def __init__(self, *args, **kwargs):
        # Initialize the ttl value
        self.__ttl = None

        # Call Podcast's constructor (this will set ttl using setattr if
        # given as argument to the constructor, hence why self.__ttl is
        # defined before we do this)
        super().__init__(*args, **kwargs)

        # If we were to use another namespace, we would add this here:
        # self._nsmap['prefix'] = "URI"

    @property
    def ttl(self):
        """Your suggestion for how many minutes podcatchers should wait
        before refreshing the feed.

        ttl stands for "time to live".

        :type: :obj:\`int\`
        :RSS: ttl
        """
        # By using @property and @ttl.setter, we encapsulate the ttl field
        # so that we can check the value that is assigned to it.
        # If you don't need this, you could just rename self.__ttl to
        # self.ttl and remove those two methods.
        return self.__ttl

    @ttl.setter
    def ttl(self, ttl):
        # Try to convert to int
        try:
            ttl_int = int(ttl)
        except ValueError:
            raise TypeError("ttl expects an integer, got %s" % ttl)
        # Is this negative?
        if ttl_int < 0:
            raise ValueError("Negative ttl values aren't accepted, got %s"
                             % ttl_int)
        # All checks passed
        self.__ttl = ttl_int

    def _create_rss(self):
        # Let Podcast generate the lxml etree (adding the standard elements)
        rss = super()._create_rss()
        # We must get the channel element, since we want to add subelements
        # to it.
        channel = rss.find("channel")
        # Only add the ttl element if it has been populated.
        if self.__ttl is not None:
            # First create our new subelement of channel.
            ttl = etree.SubElement(channel, 'ttl')
            # If we were to use another namespace, we would instead do this:
            # ttl = etree.SubElement(channel,
            #                        '{%s}ttl' % self._nsmap['prefix'])

            # Then, fill it with the ttl value
            ttl.text = str(self.__ttl)

        # Return the new etree, now with ttl
        return rss

# How to use the new class (normally, you would put this somewhere else)
if __name__ == '__main__':
    myPodcast = PodcastWithTtl(name="Test", website="http://example.org",
                               explicit=False, description="Testing ttl")
    myPodcast.ttl = 90  # or set ttl=90 in the constructor
    print(myPodcast)
```

### Using mixins

To use mixins, you cannot make the class with the `ttl` functionality inherit[`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast"). Instead, it must inherit nothing. Other than that, the code will be the same, so it doesn’t make sense to repeat it here.

```
class TtlMixin(object):
    # ...

# How to use the new mixin
class PodcastWithTtl(TtlMixin, Podcast):
    def __init__(*args, **kwargs):
        super().__init__(*args, **kwargs)

myPodcast = PodcastWithTtl(name="Test", website="http://example.org",
                           explicit=False, description="Testing ttl")
myPodcast.ttl = 90
print(myPodcast)
```

Note the order of the mixins in the class declaration. You should read it as the path Python takes when looking for a method. First Python checks`PodcastWithTtl`, then `TtlMixin` and finally [`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast"). This is also the order the methods are called when chained together using [`super()`](https://docs.python.org/3/library/functions.html#super "(in Python v3.8)"). If you had Podcast first, `Podcast._create_rss()` method would be run first, and since it never calls `super()._create_rss()`, the `TtlMixin`’s`_create_rss` would never be run. Therefore, you should always have[`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast") last in that list.

### Which approach is best?

The advantage of mixins isn’t really displayed here, but it will become apparent as you add more and more extensions. Say you define 5 different mixins, which all add exactly one more element to [`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast"). If you used traditional inheritance, you would have to make sure each of those 5 subclasses made up a tree. That is, class 1 would inherit [`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast"). Class 2 would have to inherit class 1, class 3 would have to inherit class 2 and so on. If two of the classes had the same superclass, you could get screwed.

By using mixins, you can put them together however you want. Perhaps for one podcast you only need `ttl`, while for another podcast you want to use the`textInput` element in addition to `ttl`, and another podcast requires the`textInput` element together with the `comments` element. Using traditional inheritance, you would have to duplicate code for `textInput` in two classes. Not so with mixins:

```
class PodcastWithTtl(TtlMixin, Podcast):
    def __init__(*args, **kwargs):
        super().__init__(*args, **kwargs)

class PodcastWithTtlAndTextInput(TtlMixin, TextInputMixin, Podcast):
    def __init__(*args, **kwargs):
        super().__init__(*args, **kwargs)

class PodcastWithTextInputAndComments(TextInputMixin, CommentsMixin,
                                      Podcast):
    def __init__(*args, **kwargs):
        super().__init__(*args, **kwargs)
```

If the list of elements you want to use varies between different podcasts, mixins are the way to go. On the other hand, mixins are overkill if you are okay with one giant class with all the elements you need.


## Using PubSubHubbub

PubSubHubbub is a free and open protocol for pushing updates to clients when there’s new content available in the feed, as opposed to the traditional polling clients do.

Read about [what PubSubHubbub is](https://en.wikipedia.org/wiki/PubSubHubbub) before you continue.

Note

While the protocol supports having multiple PubSubHubbub hubs for a single Podcast, there is no support for this in PodGen at the moment.

Warning

Read through the whole guide at least once before you start implementing this. Specifically, you must *not* set the [`pubsubhubbub`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.pubsubhubbub "podgen.Podcast.pubsubhubbub")attribute if you haven’t got a way to notify hubs of new episodes.

---

Contents

## Step 1: Set feed\_url

First, you must ensure that the [`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast") object has the[`feed_url`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.feed_url "podgen.Podcast.feed_url") attribute set to the URL at which the feed is accessible.

```
# Assume p is a Podcast object
p.feed_url = "https://example.com/feeds/examplefeed.rss"
```

## Step 2: Decide on a hub

The [Wikipedia article](https://en.wikipedia.org/wiki/PubSubHubbub#Usage) mentions a few options you can use (called Community Hosted hub providers). Alternatively, you can set up and host your own server using one of the open source alternatives, like for instance [Switchboard](https://github.com/aaronpk/Switchboard).

## Step 3: Set pubsubhubbub

The Podcast must contain information about which hub to use. You do this by setting [`pubsubhubbub`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.pubsubhubbub "podgen.Podcast.pubsubhubbub") to the URL which the hub is available at.

```
p.pubsubhubbub = "https://pubsubhubbub.example.com/"
```

## Step 4: Set HTTP Link Header

In addition to embedding the PubSubHubbub hub URL and the feed’s URL in the RSS itself, you should use the[Link header](https://tools.ietf.org/html/rfc5988#page-6) in the HTTP response that is sent with this feed, duplicating the link to the PubSubHubbub and the feed. Example of what it might look like:

```
Link: <https://link.to.pubsubhubbub.example.org/>; rel="hub",
      <https://example.org/podcast.rss>; rel="self"
```

How you can achieve this varies from framework to framework. Here is an example using [Flask](http://flask.pocoo.org/) (assuming the code is inside a view function):

```
from flask import make_response
from podgen import Podcast
# ...
@app.route("/<feedname>")  # Just as an example
def show_feed(feedname):
    p = Podcast()
    # ...
    # This is the relevant part:
    response = make_response(str(p))
    response.headers.add("Link", "<%s>" % p.pubsubhubbub, rel="hub")
    response.headers.add("Link", "<%s>" % p.feed_url, rel="self")
    return response
```

This is necessary for compatibility with the different versions of PubSubHubbub. The [latest version of the standard](http://pubsubhubbub.github.io/PubSubHubbub/pubsubhubbub-core-0.4.html#rfc.section.4) specifically says that publishers MUST use the Link header. If you’re unable to do this, you can try publishing the feed without; most clients and hubs should manage just fine.

## Step 5: Notify the hub of new episodes

Warning

The hub won’t know that you’ve published new episodes unless you tell it about it. If you don’t do this, the hub will assume there is no new content, and clients which trust the hub to inform them of new episodes will think there is no new content either. **Don’t set the pubsubhubbub field if you haven’t set this up yet.**

Different hubs have different ways of notifying it of new episodes. That’s why you must notify the hubs yourself; supporting all hubs is out of scope for PodGen.

If you use the [Google PubSubHubbub](https://pubsubhubbub.appspot.com/) or the [Superfeedr hub](https://pubsubhubbub.superfeedr.com/), there is a pip package called [PubSubHubbub\_Publisher](https://pypi.python.org/pypi/PubSubHubbub_Publisher) which provides this functionality for you. Example:

```
from pubsubhubbub_publish import publish, PublishError
from podgen import Podcast
# ...
try:
    publish(p.pubsubhubbub, p.feed_url)
except PublishError as e:
    # Handle error
```

In all other cases, you’re encouraged to use [Requests](http://docs.python-requests.org/) to make the necessary[POST request](http://docs.python-requests.org/en/master/user/quickstart/#make-a-request) (if no publisher package is available).

Note

If you have changes in multiple feeds, you can usually send just one single notification to the hub with all the feeds’ URLs included. It is worth researching, as it can save both you and the hub a lot of time.


## API Documentation

| [`podgen.Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast") (\*\*kwargs) | Class representing one podcast feed. |
| --- | --- |
| [`podgen.Episode`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode "podgen.Episode") (\*\*kwargs) | Class representing an episode in a podcast. |
| [`podgen.Person`](https://podgen.readthedocs.io/en/latest/api.person.html#podgen.Person "podgen.Person") (\[name, email\]) | Data-oriented class representing a single person or entity. |
| [`podgen.Media`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media "podgen.Media") (url\[, size, type, duration, …\]) | Data-oriented class representing a pointer to a media file. |
| [`podgen.Category`](https://podgen.readthedocs.io/en/latest/api.category.html#podgen.Category "podgen.Category") (category\[, subcategory\]) | Immutable class representing an Apple Podcasts category. |
| [`podgen.warnings`](https://podgen.readthedocs.io/en/latest/api.warnings.html#module-podgen.warnings "podgen.warnings") | podgen.warnings |
| [`podgen.util`](https://podgen.readthedocs.io/en/latest/api.util.html#module-podgen.util "podgen.util") | podgen.util |


## podgen.Podcast

*class* `podgen.``Podcast`(*\*\*kwargs*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/podcast.html#Podcast)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast "Permalink to this definition")

Class representing one podcast feed.

The following attributes are mandatory:

All attributes can be assigned [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)") in addition to the types specified below. Types etc. are checked during assignment, to help you discover errors earlier. Duck typing is employed wherever a class in podgen is expected.

There is a **shortcut** you can use when creating new Podcast objects, that lets you populate the attributes using the constructor. Use keyword arguments with the **attribute name as keyword** and the desired value as value. As an example:

```
>>> import podgen
>>> # The following...
>>> p = Podcast()
>>> p.name = "The Test Podcast"
>>> p.website = "http://example.com"
>>> # ...is the same as this:
>>> p = Podcast(
...     name="The Test Podcast",
...     website="http://example.com",
... )
```

Of course, you can do this for as many (or few) attributes as you like, and you can still set the attributes afterwards, like always.

| Raises: | TypeError if you use a keyword which isn’t recognized as an attribute. ValueError if you use a value which isn’t compatible with the attribute (just like when you assign it manually). |
| --- | --- |

`add_episode`(*new\_episode=None*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/podcast.html#Podcast.add_episode)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.add_episode "Permalink to this definition")

Shorthand method which adds a new episode to the feed, creating an object if it’s not provided, and returns it. This is the easiest way to add episodes to a podcast.

| Parameters: | **new\_episode** – [`Episode`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode "podgen.Episode") object to add. A new instance of is used if `new_episode` is omitted. |
| --- | --- |
| Returns: | Episode object created or passed to this function. |

Example:

```
...
>>> episode1 = p.add_episode()
>>> episode1.title = 'First episode'
>>> # You may also provide an episode object yourself:
>>> another_episode = p.add_episode(podgen.Episode())
>>> another_episode.title = 'My second episode'
```

Internally, this method creates a new instance of`episode_class`, which means you can change what type of objects are created by changing`episode_class`.

`apply_episode_order`()[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/podcast.html#Podcast.apply_episode_order)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.apply_episode_order "Permalink to this definition")

Make sure that the episodes appear on iTunes in the exact order they have in .

This will set each [`Episode.position`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.position "podgen.Episode.position") so it matches the episode’s position in .

If you’re using some [`Episode`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode "podgen.Episode") objects in multiple podcast feeds and you don’t use this method with every feed, you might want to call after generating this feed’s RSS so an episode’s position in this feed won’t affect its position in the other feeds.

`authors`

List of [`Person`](https://podgen.readthedocs.io/en/latest/api.person.html#podgen.Person "podgen.Person") that are responsible for this podcast’s editorial content.

Any value you assign to authors will be automatically converted to a list, but only if it’s iterable (like tuple, set and so on). It is an error to assign a single `Person` object to this attribute:

```
>>> # This results in an error
>>> p.authors = Person("John Doe", "johndoe@example.org")
TypeError: Only iterable types can be assigned to authors, ...
>>> # This is the correct way:
>>> p.authors = [Person("John Doe", "johndoe@example.org")]
```

The authors don’t need to have both name and email set. The names are shown under the podcast’s title on iTunes.

The initial value is an empty list, so you can use the list methods right away.

Example:

```
>>> # This attribute is just a list - you can for example append:
>>> p.authors.append(Person("John Doe", "johndoe@example.org"))
>>> # Or they can be given as new list (overriding earlier authors)
>>> p.authors = [Person("John Doe", "johndoe@example.org"),
...               Person("Mary Sue", "marysue@example.org")]
```

| Type: | [`list`](https://docs.python.org/3/library/stdtypes.html#list "(in Python v3.8)") of [`podgen.Person`](https://podgen.readthedocs.io/en/latest/api.person.html#podgen.Person "podgen.Person") |
| --- | --- |
| RSS: | managingEditor or dc:creator, and itunes:author |

`category`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.category "Permalink to this definition")

The iTunes category, which appears in the category column and in iTunes Store listings.

| Type: | [`podgen.Category`](https://podgen.readthedocs.io/en/latest/api.category.html#podgen.Category "podgen.Category") |
| --- | --- |
| RSS: | itunes:category |

`clear_episode_order`()[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/podcast.html#Podcast.clear_episode_order)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.clear_episode_order "Permalink to this definition")

Reset [`Episode.position`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode.position "podgen.Episode.position") for every single episode.

Use this if you want to reuse an [`Episode`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode "podgen.Episode") object in another feed, and don’t want its position in this feed to affect where it appears in the other feed. This is not needed if you’ll call on the other feed, though.

`cloud`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.cloud "Permalink to this definition")

The cloud data of the feed, as a 5-tuple. It specifies a web service that supports the (somewhat dated) rssCloud interface, which can be implemented in HTTP-POST, XML-RPC or SOAP 1.1.

The tuple should look like this: `(domain, port, path, registerProcedure, protocol)`.

<table><colgroup><col> <col></colgroup><tbody><tr><th>Domain:</th><td>The domain where the webservice can be found.</td></tr><tr><th>Port:</th><td>The port the webservice listens to.</td></tr><tr><th>Path:</th><td>The path of the webservice.</td></tr><tr><th colspan="2">RegisterProcedure:</th></tr><tr><td></td><td>The procedure to call.</td></tr><tr><th>Protocol:</th><td>Can be either “HTTP-POST”, “xml-rpc” or “soap”.</td></tr></tbody></table>

Example:

```
p.cloud = ("podcast.example.org", 80, "/rpc", "cloud.notify",
        "xml-rpc")
```

| Type: | [`tuple`](https://docs.python.org/3/library/stdtypes.html#tuple "(in Python v3.8)") with ( [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)"), [`int`](https://docs.python.org/3/library/functions.html#int "(in Python v3.8)"), [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)"),[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)"), [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") ) |
| --- | --- |
| RSS: | cloud |

Tip

PubSubHubbub is a competitor to rssCloud, and is the preferred choice if you’re looking to set up a new service of this kind.

`complete`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.complete "Permalink to this definition")

Whether this podcast is completed or not.

If you set this to `True`, you are indicating that no more episodes will be added to the podcast. If you let this be `None` or`False`, you are indicating that new episodes may be posted.

| Type: | [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") |
| --- | --- |
| RSS: | itunes:complete |

Warning

Setting this to `True` is the same as promising you’ll never ever release a new episode. Do NOT set this to `True` as long as there’s any chance AT ALL that a new episode will be released someday.

`copyright` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.copyright "Permalink to this definition")

The copyright notice for content in this podcast.

This should be human-readable. For example, “Copyright 2016 Example Radio”.

Note that even if you leave out the copyright notice, your content is still protected by copyright (unless anything else is indicated), since you do not need a copyright statement for something to be protected by copyright. If you intend to put the podcast in public domain or license it under a Creative Commons license, you should say so in the copyright notice.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | copyright |

`description` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.description "Permalink to this definition")

The description of the podcast, which is a phrase or sentence describing it to potential new subscribers. It is mandatory for RSS feeds, and is shown under the podcast’s name on the iTunes store page.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | description |

`episode_class`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.episode_class "Permalink to this definition")

Class used to represent episodes.

This is used by when creating new episode objects, and you, too, may use it when creating episodes.

By default, this property points to [`Episode`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode "podgen.Episode").

When assigning a new class to `episode_class`, you must make sure that the new value (1) is a class and not an instance, and (2) that it is a subclass of Episode (or is Episode itself).

Example of use:

```
>>> # Create new podcast
>>> from podgen import Podcast, Episode
>>> p = Podcast()

>>> # Normal way of creating new episodes
>>> episode1 = Episode()
>>> p.episodes.append(episode1)

>>> # Or use add_episode (and thus episode_class indirectly)
>>> episode2 = p.add_episode()

>>> # Or use episode_class directly
>>> episode3 = p.episode_class()
>>> p.episodes.append(episode3)

>>> # Say you want to use AlternateEpisode class instead of Episode
>>> from mymodule import AlternateEpisode
>>> p.episode_class = AlternateEpisode

>>> episode4 = p.add_episode()
>>> episode4.title("This is an instance of AlternateEpisode!")
```

| Type: | `class` which extends [`podgen.Episode`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode "podgen.Episode") |
| --- | --- |

`episodes`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.episodes "Permalink to this definition")

List of [`Episode`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode "podgen.Episode") objects that are part of this podcast.

See for an easy way to create new episodes and assign them to this podcast in one call.

| Type: | [`list`](https://docs.python.org/3/library/stdtypes.html#list "(in Python v3.8)") of [`podgen.Episode`](https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode "podgen.Episode") |
| --- | --- |
| RSS: | item elements |

`explicit` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.explicit "Permalink to this definition")

Whether this podcast may be inappropriate for children or not.

This is one of the mandatory attributes, and can seen as the default for episodes. Individual episodes can be marked as explicit or clean independently from the podcast.

If you set this to `True`, an “explicit” parental advisory graphic will appear next to your podcast artwork on the iTunes Store and in the Name column in iTunes. If it is set to `False`, the parental advisory type is considered Clean, meaning that no explicit language or adult content is included anywhere in the episodes, and a “clean” graphic will appear.

| Type: | [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") |
| --- | --- |
| RSS: | itunes:explicit |

`feed_url`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.feed_url "Permalink to this definition")

The URL which this feed is available at.

Identifying a feed’s URL within the feed makes it more portable, self-contained, and easier to cache. You should therefore set this attribute if you’re able to.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | atom:link with `rel="self"` |

`generator` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.generator "Permalink to this definition")

A string identifying the software that generated this RSS feed. Defaults to a string identifying PodGen.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | generator |

See also

The method

A convenient way to set the generator value and include version and url.

`image`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.image "Permalink to this definition")

The URL of the artwork for this podcast. iTunes prefers square images that are at least `1400x1400` pixels. Podcasts with an image smaller than this are *not* eligible to be featured on the iTunes Store.

iTunes supports images in JPEG and PNG formats with an RGB color space (CMYK is not supported). The URL must end in “.jpg” or “.png”; if they don’t, a [`NotSupportedByItunesWarning`](https://podgen.readthedocs.io/en/latest/api.warnings.html#podgen.warnings.NotSupportedByItunesWarning "podgen.warnings.NotSupportedByItunesWarning") will be issued.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | itunes:image |

Note

If you change your podcast’s image, you must also change the file’s name; iTunes doesn’t check the image to see if it has changed.

Additionally, the server hosting your cover art image must allow HTTP HEAD requests (most servers support this).

`language` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.language "Permalink to this definition")

The language of the podcast.

This allows aggregators to group all Italian language podcasts, for example, on a single page.

It must be a two-letter code, as found in ISO639-1, with the possibility of specifying subcodes (eg. en-US for American English). See [http://www.rssboard.org/rss-language-codes](http://www.rssboard.org/rss-language-codes) and[http://www.loc.gov/standards/iso639-2/php/code\_list.php](http://www.loc.gov/standards/iso639-2/php/code_list.php)

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | language |

`last_updated`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.last_updated "Permalink to this definition")

The last time the feed was generated. It defaults to the time and date at which the RSS is generated, if set to [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)"). The default should be sufficient for most, if not all, use cases.

The value can either be a string, which will automatically be parsed into a [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)") object when assigned, or a[`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)") object. In any case, the time and date must be timezone aware.

Set this to `False` to leave out this element instead of using the default.

| Type: | [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)"), [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") (will be converted to and stored as [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)") ), [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)") for default or [`False`](https://docs.python.org/3/library/constants.html#False "(in Python v3.8)") to leave out. |
| --- | --- |
| RSS: | lastBuildDate |

`name` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.name "Permalink to this definition")

The name of the podcast as a [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)"). It should be a human readable title. Often the same as the title of the associated website. This is mandatory and must not be blank.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | title |

`new_feed_url` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.new_feed_url "Permalink to this definition")

When set, tell iTunes that your feed has moved to this URL.

After adding this attribute, you should maintain the old feed for 48 hours before retiring it. At that point, iTunes will have updated the directory with the new feed URL.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | itunes:new-feed-url |

Warning

iTunes supports this mechanic of changing your feed’s location. However, you cannot assume the same of everyone else who has subscribed to this podcast. Therefore, you should NEVER stop supporting an old location for your podcast. Instead, you should create HTTP redirects so those with the old address are redirected to your new address, and keep those redirects up for all eternity.

Warning

Make sure the new URL you set is correct, or else you’re making people switch to a URL that doesn’t work!

`owner`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.owner "Permalink to this definition")

The [`Person`](https://podgen.readthedocs.io/en/latest/api.person.html#podgen.Person "podgen.Person") who owns this podcast. iTunes will use this person’s name and email address for all correspondence related to this podcast. It will not be publicly displayed, but it’s still publicly available in the RSS source.

Both the name and email are required.

| Type: | [`podgen.Person`](https://podgen.readthedocs.io/en/latest/api.person.html#podgen.Person "podgen.Person") |
| --- | --- |
| RSS: | itunes:owner |

`publication_date`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.publication_date "Permalink to this definition")

The publication date for the content in this podcast. You probably want to use the default value.

| Default value: | If this is [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)") when the feed is generated, the publication date of the episode with the latest publication date (which may be in the future) is used. If there are no episodes, the publication date is omitted from the feed. |
| --- | --- |

If you set this to a [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)"), it will be parsed and made into a[`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)") object when assigned. You may also set it to a [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)") object directly. In any case, the time and date must be timezone aware.

If you want to forcefully omit the publication date from the feed, set this to `False`.

| Type: | [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)"), [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") (will be converted to and stored as [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)") ), [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)") for default or [`False`](https://docs.python.org/3/library/constants.html#False "(in Python v3.8)") to leave out. |
| --- | --- |
| RSS: | pubDate |

`pubsubhubbub` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.pubsubhubbub "Permalink to this definition")

The URL at which the [PubSubHubbub](https://en.wikipedia.org/wiki/PubSubHubbub) hub can be found.

Podcatchers can tell the hub that they want to be notified when a new episode is released. This way, they don’t need to check for new episodes every few hours; instead, the episodes arrive at their doorstep as soon as they’re published, through a notification sent by the hub.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | atom:link with `rel="hub"` |

Warning

Do NOT set this attribute if you haven’t set up mechanics for notifying the hub of new episodes. Doing so could make it appear to your listeners like there is no new content for this feed. See the guide.

See also

The [guide on how to use PubSubHubbub](https://podgen.readthedocs.io/en/latest/advanced/pubsubhubbub.html)

A step-for-step guide with examples.

`rss_file`(*filename*, *minimize=False*, *encoding='UTF-8'*, *xml\_declaration=True*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/podcast.html#Podcast.rss_file)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.rss_file "Permalink to this definition")

Generate an RSS feed and write the resulting XML to a file.

Note

If atomicity is needed, then you are expected to provide that yourself. That means that you should write the feed to a temporary file which you rename to the final name afterwards; renaming is an atomic operation on Unix(like) systems.

Note

File-like objects given to this method will not be closed.

| Parameters: | - **filename** ( [*str*](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") *or* *fd* ) – Name of file to write, or a file-like object (accepting string/unicode, not bytes). - **minimize** ( [*bool*](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") ) – Set to True to disable splitting the feed into multiple lines and adding properly indentation, saving bytes at the cost of readability (default: False). - **encoding** ( [*str*](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") ) – Encoding used in the XML file (default: UTF-8). - **xml\_declaration** ( [*bool*](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") ) – Whether an XML declaration should be added to the output (default: True). |
| --- | --- |
| Returns: | Nothing. |

`rss_str`(*minimize=False*, *encoding='UTF-8'*, *xml\_declaration=True*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/podcast.html#Podcast.rss_str)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.rss_str "Permalink to this definition")

Generate an RSS feed and return the feed XML as string.

| Parameters: | - **minimize** ( [*bool*](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") ) – Set to True to disable splitting the feed into multiple lines and adding properly indentation, saving bytes at the cost of readability (default: False). - **encoding** ( [*str*](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") ) – Encoding used in the XML declaration (default: UTF-8). - **xml\_declaration** ( [*bool*](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") ) – Whether an XML declaration should be added to the output (default: True). |
| --- | --- |
| Returns: | The generated RSS feed as a [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") (unicode in 2.7) |

`set_generator`(*generator=None*, *version=None*, *uri=None*, *exclude\_podgen=False*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/podcast.html#Podcast.set_generator)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.set_generator "Permalink to this definition")

Set the generator of the feed, formatted nicely, which identifies the software used to generate the feed.

| Parameters: | - **generator** ( [*str*](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") ) – Software used to create the feed. - **version** ( [`tuple`](https://docs.python.org/3/library/stdtypes.html#tuple "(in Python v3.8)") of [`int`](https://docs.python.org/3/library/functions.html#int "(in Python v3.8)") ) – (Optional) Version of the software, as a tuple. - **uri** ( [*str*](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") ) – (Optional) The software’s website. - **exclude\_podgen** ( [*bool*](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") ) – (Optional) Set to True if you don’t want PodGen to be mentioned (e.g., “My Program (using PodGen 1.0.0)”) |
| --- | --- |

See also

The attribute

Lets you access and set the generator string yourself, without any formatting help.

`skip_days`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.skip_days "Permalink to this definition")

Set of days in which podcatchers don’t need to refresh this feed.

This isn’t widely supported by podcatchers.

The days are represented using strings of their English names, like “Monday” or “wednesday”. The day names are automatically capitalized when the set is assigned to `skip_days`, but subsequent changes to the set “in place” are only checked and capitalized when the RSS feed is generated.

For example, to stop refreshing the feed in the weekend:

```
>>> from podgen import Podcast
>>> p = Podcast()
>>> p.skip_days = {"Friday", "Saturday", "sUnDaY"}
>>> p.skip_days
{"Saturday", "Friday", "Sunday"}
```

| Type: | [`set`](https://docs.python.org/3/library/stdtypes.html#set "(in Python v3.8)") of [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | skipDays |

`skip_hours`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.skip_hours "Permalink to this definition")

Set of hours of the day in which podcatchers don’t need to refresh this feed.

This isn’t widely supported by podcatchers.

The hours are represented as integer values from 0 to 23. Note that while the content of the set is checked when it is first assigned to `skip_hours`, further changes to the set “in place” will not be checked before you generate the RSS.

For example, to stop refreshing the feed between 18 and 7:

```
>>> from podgen import Podcast
>>> p = Podcast()
>>> p.skip_hours = set(range(18, 24))
>>> p.skip_hours
{18, 19, 20, 21, 22, 23}
>>> p.skip_hours |= set(range(8))
>>> p.skip_hours
{0, 1, 2, 3, 4, 5, 6, 7, 18, 19, 20, 21, 22, 23}
```

| Type: | [`set`](https://docs.python.org/3/library/stdtypes.html#set "(in Python v3.8)") of [`int`](https://docs.python.org/3/library/functions.html#int "(in Python v3.8)") |
| --- | --- |
| RSS: | skipHours |

`subtitle` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.subtitle "Permalink to this definition")

The subtitle for your podcast, shown mainly as a very short description on iTunes. The subtitle displays best if it is only a few words long, like a short slogan.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | itunes:subtitle |

`web_master`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.web_master "Permalink to this definition")

The [`Person`](https://podgen.readthedocs.io/en/latest/api.person.html#podgen.Person "podgen.Person") responsible for technical issues relating to the feed.

| Type: | [`podgen.Person`](https://podgen.readthedocs.io/en/latest/api.person.html#podgen.Person "podgen.Person") |
| --- | --- |
| RSS: | webMaster |

`website` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.website "Permalink to this definition")

The absolute URL of this podcast’s website.

This is one of the mandatory attributes.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | link |

`withhold_from_itunes` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.withhold_from_itunes "Permalink to this definition")

Prevent the entire podcast from appearing in the iTunes podcast directory.

Note that this will affect more than iTunes, since most podcatchers use the iTunes catalogue to implement the search feature. Listeners will still be able to subscribe by adding the feed’s address manually.

If you don’t intend to submit this podcast to iTunes, you can set this to `True` as a way of giving iTunes the middle finger, and perhaps more importantly, preventing others from submitting it as well.

Set it to `True` to withhold the entire podcast from iTunes. It is set to `False` by default, of course.

| Type: | [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") |
| --- | --- |
| RSS: | itunes:block |

`xslt` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Podcast.xslt "Permalink to this definition")

Absolute URL to the XSLT file which web browsers should use with this feed.

[XSLT](https://en.wikipedia.org/wiki/XSLT) stands for Extensible Stylesheet Language Transformations and can be regarded as a template language made for transforming XML into XHTML (among other things). You can use it to avoid giving users an ugly XML listing when trying to subscribe to your podcast; this technique is in fact employed by most podcast publishers today. In a web browser, it looks like a web page, and to the podcatchers, it looks like a normal podcast feed. To put it another way, the very same URL can be used as an information web page about the podcast as well as the URL you subscribe to in podcatchers.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | Processor instruction right after the xml declaration called `xml-stylesheet`, with type set to `text/xsl` and href set to this attribute. |


## podgen.Episode

*class* `podgen.``Episode`(*\*\*kwargs*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/episode.html#Episode)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode "Permalink to this definition")

Class representing an episode in a podcast. Corresponds to an RSS Item.

When creating a new Episode, you can populate any attribute using keyword arguments. Use the attribute’s name on the left side of the equals sign and its value on the right side. Here’s an example:

```
>>> # This...
>>> ep = Episode()
>>> ep.title = "Exploring the RTS genre"
>>> ep.summary = "Tory and I talk about a genre of games we've " + \
...              "never dared try out before now..."
>>> # ...is equal to this:
>>> ep = Episode(
...    title="Exploring the RTS genre",
...    summary="Tory and I talk about a genre of games we've "
...            "never dared try out before now..."
... )
```

| Raises: | TypeError if you try to set an attribute which doesn’t exist, ValueError if you set an attribute to an invalid value. |
| --- | --- |

You must have filled in either or before the RSS can be generated.

To add an episode to a podcast:

```
>>> import podgen
>>> p = podgen.Podcast()
>>> episode = podgen.Episode()
>>> p.episodes.append(episode)
```

You may also replace the last two lines with a shortcut:

```
>>> episode = p.add_episode(podgen.Episode())
```

See also

[Episodes](https://podgen.readthedocs.io/en/latest/usage_guide/episodes.html)

A friendlier introduction to episodes.

`authors`

List of [`Person`](https://podgen.readthedocs.io/en/latest/api.person.html#podgen.Person "podgen.Person") that contributed to this episode.

The authors don’t need to have both name and email set. They’re usually not displayed anywhere.

Note

You do not need to provide any authors for an episode if they’re identical to the podcast’s authors.

Any value you assign to authors will be automatically converted to a list, but only if it’s iterable (like tuple, set and so on). It is an error to assign a single [`Person`](https://podgen.readthedocs.io/en/latest/api.person.html#podgen.Person "podgen.Person") object to this attribute:

```
>>> # This results in an error
>>> ep.authors = Person("John Doe", "johndoe@example.org")
TypeError: Only iterable types can be assigned to authors, ...
>>> # This is the correct way:
>>> ep.authors = [Person("John Doe", "johndoe@example.org")]
```

The initial value is an empty list, so you can use the list methods right away.

Example:

```
>>> # This attribute is just a list - you can for example append:
>>> ep.authors.append(Person("John Doe", "johndoe@example.org"))
>>> # Or assign a new list (discarding earlier authors)
>>> ep.authors = [Person("John Doe", "johndoe@example.org"),
...               Person("Mary Sue", "marysue@example.org")]
```

| Type: | [`list`](https://docs.python.org/3/library/stdtypes.html#list "(in Python v3.8)") of [`podgen.Person`](https://podgen.readthedocs.io/en/latest/api.person.html#podgen.Person "podgen.Person") |
| --- | --- |
| RSS: | author or dc:creator, and itunes:author |

`explicit`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.explicit "Permalink to this definition")

Whether this podcast episode contains material which may be inappropriate for children.

The value of the podcast’s explicit attribute is used by default, if this is kept as `None`.

If you set this to `True`, an “explicit” parental advisory graphic will appear in the Name column in iTunes. If the value is`False`, the parental advisory type is considered Clean, meaning that no explicit language or adult content is included anywhere in this episode, and a “clean” graphic will appear.

| Type: | [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") |
| --- | --- |
| RSS: | itunes:explicit |

`id` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.id "Permalink to this definition")

This episode’s globally unique identifier.

If not present, the URL of the enclosed media is used. This is usually the best way to go, **as long as the media URL doesn’t change**.

Set the id to boolean `False` if you don’t want to associate any id to this episode.

It is important that an episode keeps the same ID until the end of time, since the ID is used by clients to identify which episodes have been listened to, which episodes are new, and so on. Changing the ID causes the same consequences as deleting the existing episode and adding a new, identical episode.

Note that this is a GLOBALLY unique identifier. Thus, not only must it be unique in this podcast, it must not be the same ID as any other episode for any podcast out there. To ensure this, you should use a domain which you own (for example, use something like[http://example.org/podcast/episode1](http://example.org/podcast/episode1) if you own example.org).

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)"), [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)") to use default or [`False`](https://docs.python.org/3/library/constants.html#False "(in Python v3.8)") to leave out. |
| --- | --- |
| RSS: | guid |

`image`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.image "Permalink to this definition")

The podcast episode’s image, overriding the podcast’s[`image`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.image "podgen.Podcast.image").

This attribute specifies the absolute URL to the artwork for your podcast. iTunes prefers square images that are at least `1400x1400`pixels.

iTunes supports images in JPEG and PNG formats with an RGB color space (CMYK is not supported). The URL must end in “.jpg” or “.png”; a[`NotSupportedByItunesWarning`](https://podgen.readthedocs.io/en/latest/api.warnings.html#podgen.warnings.NotSupportedByItunesWarning "podgen.warnings.NotSupportedByItunesWarning") will be issued if it doesn’t.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | itunes:image |

Note

If you change an episode’s image, you should also change the file’s name; iTunes doesn’t check the actual file to see if it’s changed.

Additionally, the server hosting your cover art image must allow HTTP HEAD requests.

Warning

Almost no podcatchers support this. iTunes supports it only if you embed the cover in the media file (the same way you would embed an album cover), and recommends that you use Garageband’s Enhanced Podcast feature.

The podcast’s image is used if this isn’t supported.

`is_closed_captioned` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.is_closed_captioned "Permalink to this definition")

Whether this podcast includes a video episode with embedded [closed captioning](https://en.wikipedia.org/wiki/Closed_captioning) support. Defaults to `False`.

| Type: | [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") |
| --- | --- |
| RSS: | itunes:isClosedCaptioned |

`link` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.link "Permalink to this definition")

The link to the full version of this episode’s . Remember to start the link with the scheme, e.g. [https://](https://).

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | link |

`long_summary` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.long_summary "Permalink to this definition")

A long (read: full) summary, which supplements the shorter. Like summary, this must be compatible with XHTML parsers; use `podgen.htmlencode()` if this isn’t HTML.

This attribute should be seen as a full, longer variation of summary if summary exists. Even then, the long\_summary should be independent from summary, in that you only need to read one of them. This means you may have to repeat the first sentences.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") which can be parsed as XHTML. |
| --- | --- |
| RSS: | content:encoded or description |

`media`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.media "Permalink to this definition")

Get or set the [`Media`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media "podgen.Media") object that is attached to this episode.

Note that if is not set, the media’s URL is used as the id. If you rely on this, you should make sure the URL never changes, since changing the id messes up with clients (they will think this episode is new again, even if the user has listened to it already). Therefore, you should only rely on this behaviour if you own the domain which the episodes reside on. If you don’t, then you must set to an appropriate value manually.

| Type: | [`podgen.Media`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media "podgen.Media") |
| --- | --- |
| RSS: | enclosure and itunes:duration |

`position`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.position "Permalink to this definition")

A custom position for this episode on the iTunes store page.

If you would like this episode to appear first, set it to `1`. If you want it second, set it to `2`, and so on. If multiple episodes share the same position, they will be sorted by their.

To remove the order from the episode, set the position back to[`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)").

| Type: | [`int`](https://docs.python.org/3/library/functions.html#int "(in Python v3.8)") |
| --- | --- |
| RSS: | itunes:order |

`publication_date`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.publication_date "Permalink to this definition")

The time and date this episode was first published.

The value can be a [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)"), which will be parsed and made into a [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)") object when assigned. You may also assign a [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)") object directly. In both cases, you must ensure that the value includes timezone information.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") (will be converted to and stored as [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)") ) or [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)"). |
| --- | --- |
| RSS: | pubDate |

Note

Don’t use the media file’s modification date as the publication date, unless they’re the same. It looks very odd when an episode suddenly pops up in the feed, but it claims to be several hours old!

`rss_entry`()[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/episode.html#Episode.rss_entry)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.rss_entry "Permalink to this definition")

Create an RSS item using lxml’s etree and return it.

This is primarily used by [`podgen.Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast") when generating the podcast’s RSS feed.

| Returns: | etree.Element(‘item’) |
| --- | --- |

`subtitle` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.subtitle "Permalink to this definition")

A short subtitle.

This is shown in the Description column in iTunes. The subtitle displays best if it is only a few words long.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | itunes:subtitle |

`summary` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.summary "Permalink to this definition")

The summary of this episode, in a format that can be parsed by XHTML parsers.

If your summary isn’t fit to be parsed as XHTML, you can use`podgen.htmlencode()` to fix the text, like this:

```
>>> ep.summary = podgen.htmlencode("We spread lots of love <3")
>>> ep.summary
We spread lots of love &lt;3
```

In iTunes, the summary is shown in a separate window that appears when the “circled i” in the Description column is clicked. This field can be up to 4000 characters in length.

See also and.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") which can be parsed as XHTML. |
| --- | --- |
| RSS: | description |

`title` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.title "Permalink to this definition")

This episode’s human-readable title. Title is mandatory and should not be blank.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |
| RSS: | title |

`withhold_from_itunes`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.withhold_from_itunes "Permalink to this definition")

Prevent this episode from appearing in the iTunes podcast directory. Note that the episode can still be found by inspecting the XML, so it is still public.

One use case would be if you knew that this episode would get you kicked out from iTunes, should it make it there. In such cases, you can set withhold\_from\_itunes to `True` so this episode isn’t published on iTunes, allowing you to publish it to everyone else while keeping your podcast on iTunes.

This attribute defaults to `False`, of course.

| Type: | [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") |
| --- | --- |
| RSS: | itunes:block |


## podgen.Person

*class* `podgen.``Person`(*name=None*, *email=None*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/person.html#Person)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Person "Permalink to this definition")

Data-oriented class representing a single person or entity.

A Person can represent both real persons and less personal entities like organizations. Example:

```
>>> p.authors = [Person("Example Radio", "mail@example.org")]
```

Note

At any time, one of name or email must be present. Both cannot be None or empty at the same time.

Warning

**Any names and email addresses** you put into a Person object will eventually be included and **published** together with the feed. If you want to keep a name or email address private, then you must make sure it isn’t used in a Person object (or to be precise: that the Person object with the name or email address isn’t used in any Podcast or Episode.)

Example of use:

```
>>> from podgen import Person
>>> Person("John Doe")
Person(name=John Doe, email=None)
>>> Person(email="johndoe@example.org")
Person(name=None, email=johndoe@example.org)
>>> Person()
ValueError: You must provide either a name or an email address.
```

`email`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Person.email "Permalink to this definition")

This person’s public email address.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |

`name`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Person.name "Permalink to this definition")

This person’s name.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |


## podgen.Media

*class* `podgen.``Media`(*url*, *size=0*, *type=None*, *duration=None*, *requests\_session=None*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/media.html#Media)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Media "Permalink to this definition")

Data-oriented class representing a pointer to a media file.

A media file can be a sound file (most typical), video file or a document.

You should provide the absolute URL at which this media can be found, and the media’s file size in bytes.

Optionally, you can provide the type of media (expressed using MIME types). When not given in the constructor, it will be found automatically by looking at the url’s file extension. If the url’s file extension isn’t supported by iTunes, you will get an error if you don’t supply the type.

You are also highly encouraged to provide the duration of the media.

Note

iTunes is lazy and will just look at the URL to figure out if a file is of a supported file type. You must therefore ensure your URL ends with a supported file extension.

Note

A warning called [`NotSupportedByItunesWarning`](https://podgen.readthedocs.io/en/latest/api.warnings.html#podgen.warnings.NotSupportedByItunesWarning "podgen.warnings.NotSupportedByItunesWarning")will be issued if your URL or type isn’t compatible with iTunes. See the Python documentation for more details on [`warnings`](https://docs.python.org/3/library/warnings.html#module-warnings "(in Python v3.8)").

Media types supported by iTunes:

- Audio
	- M4A
	- MP3
- Video
	- MOV
	- MP4
	- M4V
- Document
	- PDF
	- EPUB

All attributes will always have a value, except size which can be 0 if the size cannot be determined by any means (eg. if it’s a stream) and duration which is optional (but recommended).

See also

[Enclosing media](https://podgen.readthedocs.io/en/latest/usage_guide/episodes.html#podgen-media-guide)

for a more gentle introduction.

*classmethod* `create_from_server_response`(*url*, *size=None*, *type=None*, *duration=None*, *requests\_=None*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/media.html#Media.create_from_server_response)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Media.create_from_server_response "Permalink to this definition")

Create new Media object, with size and/or type fetched from the server when not given.

See for a (slow!) way to fill in the duration as well.

Example (assuming the server responds with Content-Length: 252345991 and Content-Type: audio/mpeg):

```
>>> from podgen import Media
  >>> # Assume an episode is hosted at example.com
  >>> m = Media.create_from_server_response(
  ...     "http://example.com/episodes/ep1.mp3")
  >>> m
  Media(url=http://example.com/episodes/ep1.mp3, size=252345991,
type=audio/mpeg, duration=None)
```

| Parameters: | - **url** ( [*str*](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") ) – The URL at which the media can be accessed right now. - **size** ( [*int*](https://docs.python.org/3/library/functions.html#int "(in Python v3.8)") *or* [*None*](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)") ) – Size of the file. Will be fetched from server if not given. - **type** ( [*str*](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") *or* [*None*](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)") ) – The media type of the file. Will be fetched from server if not given. - **duration** ( [`datetime.timedelta`](https://docs.python.org/3/library/datetime.html#datetime.timedelta "(in Python v3.8)") or [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)") ) – The media’s duration. - **requests** ( [`requests`](https://requests.readthedocs.io/en/master/api/#module-requests "(in Requests v2.23.0)") or [`requests.Session`](https://requests.readthedocs.io/en/master/api/#requests.Session "(in Requests v2.23.0)") ) – Either the [requests](http://docs.python-requests.org/en/master/) module itself, or a [`requests.Session`](https://requests.readthedocs.io/en/master/api/#requests.Session "(in Requests v2.23.0)") object. Defaults to a new [`Session`](https://requests.readthedocs.io/en/master/api/#requests.Session "(in Requests v2.23.0)"). |
| --- | --- |
| Returns: | New instance of Media with url, size and type filled in. |
| Raises: | The appropriate requests exceptions are thrown when networking errors occur. RuntimeError is thrown if some information isn’t given and isn’t found in the server’s response. |

`download`(*destination*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/media.html#Media.download)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Media.download "Permalink to this definition")

Download the media file.

This method will block until the file is downloaded in its entirety.

Note

The destination will not be populated atomically; if you need this, you must give provide a temporary file as destination and rename the file yourself.

| Parameters: | **destination** ( `fd` or [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)").) – Where to save the media file. Either a filename, or a file-like object. The file-like object will *not* be closed by PodGen. |
| --- | --- |

`duration`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Media.duration "Permalink to this definition")

The duration of the media file.

| Type: | [`datetime.timedelta`](https://docs.python.org/3/library/datetime.html#datetime.timedelta "(in Python v3.8)") |
| --- | --- |
| Raises: | [`TypeError`](https://docs.python.org/3/library/exceptions.html#TypeError "(in Python v3.8)") if you try to assign anything other than [`datetime.timedelta`](https://docs.python.org/3/library/datetime.html#datetime.timedelta "(in Python v3.8)") or [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)") to this attribute. Raises [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError "(in Python v3.8)") if a negative timedelta value is given. |

`duration_str`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Media.duration_str "Permalink to this definition")

, formatted as a string according to iTunes’ specs. That is, HH:MM:SS if it lasts more than an hour, or MM:SS if it lasts less than an hour.

This is just an alternate, read-only view of .

If is [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)"), then this will be [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)") as well.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |

`fetch_duration`()[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/media.html#Media.fetch_duration)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Media.fetch_duration "Permalink to this definition")

Download locally and use it to populate.

Use this method when you don’t have the media file on the local file system. Use otherwise.

This method will take quite some time, since the media file must be downloaded before it can be analyzed.

`file_extension`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Media.file_extension "Permalink to this definition")

The file extension of . Read-only.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |

`get_type`(*url*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/media.html#Media.get_type)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Media.get_type "Permalink to this definition")

Guess the MIME type from the URL.

This is used to fill in when it is not given (and thus called implicitly by the constructor), but you can call it yourself.

Example:

```
>>> from podgen import Media
>>> m = Media("http://example.org/1.mp3", 136532744)
>>> # The type was detected from the url:
>>> m.type
audio/mpeg
>>> # Ops, I changed my mind...
>>> m.url = "https://example.org/1.m4a"
>>> # As you can see, the type didn't change:
>>> m.type
audio/mpeg
>>> # So update type yourself
>>> m.type = m.get_type(m.url)
>>> m.type
audio/x-m4a
```

| Parameters: | **url** ( [*str*](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") ) – The URL which should be used to guess the MIME type. |
| --- | --- |
| Returns: | The guessed MIME type. |
| Raises: | ValueError if the MIME type couldn’t be guessed from the URL. |

`populate_duration_from`(*filename*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/media.html#Media.populate_duration_from)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Media.populate_duration_from "Permalink to this definition")

Populate by analyzing the given file.

Use this method when you have the media file on the local file system. Use if you need to download the file from the server.

| Parameters: | **filename** ( [*str*](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") ) – Path to the media file which shall be used to determine this media’s duration. The file extension must match its file type, since it is used to determine what type of media file it is. For a list of supported formats, see [https://pypi.python.org/pypi/tinytag/](https://pypi.python.org/pypi/tinytag/) |
| --- | --- |

`requests_session` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Media.requests_session "Permalink to this definition")

The requests.Session object which shall be used. Defaults to a new session with PodGen as User-Agent.

This is used by the instance methods and., however, creates its own requests Session if not given as a parameter (since it is a static method).

You can set this attribute manually to set your own User-Agent and benefit from Keep-Alive across different instances of Media.

| Type: | [`requests.Session`](https://requests.readthedocs.io/en/master/api/#requests.Session "(in Requests v2.23.0)") |
| --- | --- |

`size`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Media.size "Permalink to this definition")

The media’s file size in bytes.

You can either provide the number of bytes as an [`int`](https://docs.python.org/3/library/functions.html#int "(in Python v3.8)"), or you can provide a human-readable [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") with a unit, like MB or GiB.

An unknown size is represented as 0. This should ONLY be used in exceptional cases, where it is theoretically impossible to determine the file size (for example if it’s a stream). Setting the size to 0 will issue a UserWarning.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") (which will be converted to and stored as [`int`](https://docs.python.org/3/library/functions.html#int "(in Python v3.8)") ) or [`int`](https://docs.python.org/3/library/functions.html#int "(in Python v3.8)") |
| --- | --- |

Note

If you provide a string, it will be translated to int when the assignment happens. Thus, on subsequent accesses, you will get the resulting int, not the string you put in.

Note

The units are case-insensitive. This means that the `B` is always assumed to mean “bytes”, even if it is lowercase (`b`). Likewise, `m` is taken to mean mega, not milli.

`type`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Media.type "Permalink to this definition")

The MIME type of this media.

See [https://en.wikipedia.org/wiki/Media\_type](https://en.wikipedia.org/wiki/Media_type) for an introduction.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |

Note

If you leave out type when creating a new Media object, the type will be auto-detected from the attribute. However, this won’t happen automatically other than during initialization. If you want to autodetect type when assigning a new value to url, you should use.

`url`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Media.url "Permalink to this definition")

The URL at which this media is publicly accessible.

Only absolute URLs are allowed, so make sure it starts with [http://](http://) or[https://](https://). The server should support HEAD-requests and byte-range requests.

Ensure you quote parts of the URL that are not supposed to carry any special meaning to the browser, typically the name of your file. Common offenders include the slash character when not used to separate folders, the hash mark (#) and the question mark (?). Use[`urllib.parse.quote()`](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.quote "(in Python v3.8)") in Python3 and `urllib.quote()` in Python2.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |


## podgen.Category

*class* `podgen.``Category`(*category*, *subcategory=None*)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Category "Permalink to this definition")

Immutable class representing an Apple Podcasts category.

By using this class, you can be sure that the chosen category is a valid category, that it is formatted correctly and you will be warned when using an old category.

See [https://help.apple.com/itc/podcasts\_connect/#/itc9267a2f12](https://help.apple.com/itc/podcasts_connect/#/itc9267a2f12) for an overview of the available categories and their subcategories.

Changed in version 1.1.0: Updated to reflect [the new categories](https://podnews.net/article/apple-changed-podcast-categories-2019)as of August 9th 2019 and yield a[`LegacyCategoryWarning`](https://podgen.readthedocs.io/en/latest/api.warnings.html#podgen.warnings.LegacyCategoryWarning "podgen.warnings.LegacyCategoryWarning") when using one of the old categories.

Note

The categories are case-insensitive, and you may escape ampersands. The category and subcategory will end up properly capitalized and with unescaped ampersands.

Example:

```
>>> from podgen import Category
>>> c = Category("Music")
>>> c.category
Music
>>> c.subcategory
None
>>>
>>> d = Category("games &amp; hobbies", "Video games")
>>> d.category
Games & Hobbies
>>> d.subcategory
Video Games
```

`category`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Category.category "Permalink to this definition")

The category represented by this object. Read-only.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |

`subcategory`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Category.subcategory "Permalink to this definition")

The subcategory this object represents. Read-only.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| --- | --- |


## podgen.warnings

This file contains PodGen-specific warnings. They can be imported directly from `podgen`.

| copyright: | 2019, Thorben Dahl < [thorben @ sjostrom.no](https://podgen.readthedocs.io/en/latest/) > |
| --- | --- |
| license: | FreeBSD and LGPL, see license.\* for more details. |

*exception* `podgen.warnings.``LegacyCategoryWarning`[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/warnings.html#LegacyCategoryWarning)[¶](https://podgen.readthedocs.io/en/latest/#podgen.warnings.LegacyCategoryWarning "Permalink to this definition")

Indicates that the category created is an old category. It will still be accepted by Apple Podcasts, but it would be wise to use the new categories since they may have more relevant options for your podcast.

See also

[What’s New: Enhanced Apple Podcasts Categories](https://itunespartner.apple.com/podcasts/whats-new/100002564)

Consequences of using old categories.

[Podcasts Connect Help: Apple Podcasts categories](https://help.apple.com/itc/podcasts_connect/#/itc9267a2f12)

Up-to-date list of available categories.

[Podnews: New and changed Apple Podcasts categories](https://podnews.net/article/apple-changed-podcast-categories-2019)

List of changes between the old and the new categories.

Warns against behaviour or usage which is usually discouraged. However, there may exist exceptions where there is no better way.

*exception* `podgen.warnings.``NotSupportedByItunesWarning`[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/warnings.html#NotSupportedByItunesWarning)[¶](https://podgen.readthedocs.io/en/latest/#podgen.warnings.NotSupportedByItunesWarning "Permalink to this definition")

Indicates that PodGen is used in a way that may not be compatible with Apple Podcasts (previously known as iTunes).

In some cases, this may be because PodGen has not been kept up-to-date with new features which Apple Podcasts has added support for. Please add an issue if that is the case!

*exception* `podgen.warnings.``PodgenWarning`[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/warnings.html#PodgenWarning)[¶](https://podgen.readthedocs.io/en/latest/#podgen.warnings.PodgenWarning "Permalink to this definition")

Superclass for all warnings defined by PodGen.

## podgen.util

This file contains helper functions for the feed generator module.

| copyright: | 2013, Lars Kiesow < [lkiesow @ uos.de](https://podgen.readthedocs.io/en/latest/) > and 2016, Thorben Dahl < [thorben @ sjostrom.no](https://podgen.readthedocs.io/en/latest/) > |
| --- | --- |
| license: | FreeBSD and LGPL, see license.\* for more details. |

`podgen.util.``ensure_format`(*val*, *allowed*, *required*, *allowed\_values=None*, *defaults=None*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/util.html#ensure_format)[¶](https://podgen.readthedocs.io/en/latest/#podgen.util.ensure_format "Permalink to this definition")

Takes a dictionary or a list of dictionaries and check if all keys are in the set of allowed keys, if all required keys are present and if the values of a specific key are ok.

| Parameters: | - **val** – Dictionaries to check. - **allowed** – Set of allowed keys. - **required** – Set of required keys. - **allowed\_values** – Dictionary with keys and sets of their allowed values. - **defaults** – Dictionary with default values. |
| --- | --- |
| Returns: | List of checked dictionaries. |

`podgen.util.``formatRFC2822`(*d*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/util.html#formatRFC2822)[¶](https://podgen.readthedocs.io/en/latest/#podgen.util.formatRFC2822 "Permalink to this definition")

Format a datetime according to RFC2822.

This implementation exists as a workaround to ensure that the locale setting does not interfere with the time format. For example, day names might get translated to your local language, which would break with the standard.

| Parameters: | **d** ( [*datetime.datetime*](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)") ) – Time and date you want to format according to RFC2822. |
| --- | --- |
| Returns: | The datetime formatted according to the RFC2822. |
| Return type: | [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |

`podgen.util.``htmlencode`(*s*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/util.html#htmlencode)[¶](https://podgen.readthedocs.io/en/latest/#podgen.util.htmlencode "Permalink to this definition")

Encode the given string so its content won’t be confused as HTML markup.

This function exists as a cross-version compatibility alias.

`podgen.util.``listToHumanreadableStr`(*l*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/util.html#listToHumanreadableStr)[¶](https://podgen.readthedocs.io/en/latest/#podgen.util.listToHumanreadableStr "Permalink to this definition")

Create a human-readable string out of the given iterable.

Example:

```
>>> from podgen.util import listToHumanreadableStr
>>> listToHumanreadableStr([1, 2, 3])
1, 2 and 3
```

The string `(empty)` is returned if the list is empty – it is assumed that you check whether the list is empty yourself.