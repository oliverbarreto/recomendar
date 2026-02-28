---
title: "podgen.Episode — PodGen Documentation"
source: "https://podgen.readthedocs.io/en/latest/api.episode.html#podgen.Episode"
author:
published:
created: 2025-09-27
description:
tags:
  - "clippings"
---
*class* `podgen.``Episode`(*\*\*kwargs*)[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/episode.html#Episode)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode "Permalink to this definition")

Class representing an episode in a podcast. Corresponds to an RSS Item.

When creating a new Episode, you can populate any attribute using keyword arguments. Use the attribute’s name on the left side of the equals sign and its value on the right side. Here’s an example:

```default
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
| ------- | --------------------------------------------------------------------------------------------------------------------- |

You must have filled in either [`title`](https://podgen.readthedocs.io/en/latest/#podgen.Episode.title "podgen.Episode.title") or [`summary`](https://podgen.readthedocs.io/en/latest/#podgen.Episode.summary "podgen.Episode.summary") before the RSS can be generated.

To add an episode to a podcast:

```default
>>> import podgen
>>> p = podgen.Podcast()
>>> episode = podgen.Episode()
>>> p.episodes.append(episode)
```

You may also replace the last two lines with a shortcut:

```default
>>> episode = p.add_episode(podgen.Episode())
```

See also

[Episodes](https://podgen.readthedocs.io/en/latest/usage_guide/episodes.html)

A friendlier introduction to episodes.

List of [`Person`](https://podgen.readthedocs.io/en/latest/api.person.html#podgen.Person "podgen.Person") that contributed to this episode.

The authors don’t need to have both name and email set. They’re usually not displayed anywhere.

Note

You do not need to provide any authors for an episode if they’re identical to the podcast’s authors.

Any value you assign to authors will be automatically converted to a list, but only if it’s iterable (like tuple, set and so on). It is an error to assign a single [`Person`](https://podgen.readthedocs.io/en/latest/api.person.html#podgen.Person "podgen.Person") object to this attribute:

```default
>>> # This results in an error
>>> ep.authors = Person("John Doe", "johndoe@example.org")
TypeError: Only iterable types can be assigned to authors, ...
>>> # This is the correct way:
>>> ep.authors = [Person("John Doe", "johndoe@example.org")]
```

The initial value is an empty list, so you can use the list methods right away.

Example:

```default
>>> # This attribute is just a list - you can for example append:
>>> ep.authors.append(Person("John Doe", "johndoe@example.org"))
>>> # Or assign a new list (discarding earlier authors)
>>> ep.authors = [Person("John Doe", "johndoe@example.org"),
...               Person("Mary Sue", "marysue@example.org")]
```

| Type: | [`list`](https://docs.python.org/3/library/stdtypes.html#list "(in Python v3.8)") of [`podgen.Person`](https://podgen.readthedocs.io/en/latest/api.person.html#podgen.Person "podgen.Person") |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RSS:  | author or dc:creator, and itunes:author                                                                                                                                                       |

`explicit`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.explicit "Permalink to this definition")

Whether this podcast episode contains material which may be inappropriate for children.

The value of the podcast’s explicit attribute is used by default, if this is kept as `None`.

If you set this to `True`, an “explicit” parental advisory graphic will appear in the Name column in iTunes. If the value is `False`, the parental advisory type is considered Clean, meaning that no explicit language or adult content is included anywhere in this episode, and a “clean” graphic will appear.

| Type: | [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") |
| ----- | ---------------------------------------------------------------------------------- |
| RSS:  | itunes:explicit                                                                    |

`id` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.id "Permalink to this definition")

This episode’s globally unique identifier.

If not present, the URL of the enclosed media is used. This is usually the best way to go, **as long as the media URL doesn’t change**.

Set the id to boolean `False` if you don’t want to associate any id to this episode.

It is important that an episode keeps the same ID until the end of time, since the ID is used by clients to identify which episodes have been listened to, which episodes are new, and so on. Changing the ID causes the same consequences as deleting the existing episode and adding a new, identical episode.

Note that this is a GLOBALLY unique identifier. Thus, not only must it be unique in this podcast, it must not be the same ID as any other episode for any podcast out there. To ensure this, you should use a domain which you own (for example, use something like [http://example.org/podcast/episode1](http://example.org/podcast/episode1) if you own example.org).

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)"), [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)") to use default or [`False`](https://docs.python.org/3/library/constants.html#False "(in Python v3.8)") to leave out. |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RSS:  | guid                                                                                                                                                                                                                                                                                     |

`image`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.image "Permalink to this definition")

The podcast episode’s image, overriding the podcast’s [`image`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.image "podgen.Podcast.image").

This attribute specifies the absolute URL to the artwork for your podcast. iTunes prefers square images that are at least `1400x1400` pixels.

iTunes supports images in JPEG and PNG formats with an RGB color space (CMYK is not supported). The URL must end in “.jpg” or “.png”; a [`NotSupportedByItunesWarning`](https://podgen.readthedocs.io/en/latest/api.warnings.html#podgen.warnings.NotSupportedByItunesWarning "podgen.warnings.NotSupportedByItunesWarning") will be issued if it doesn’t.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| ----- | ------------------------------------------------------------------------------- |
| RSS:  | itunes:image                                                                    |

Note

If you change an episode’s image, you should also change the file’s name; iTunes doesn’t check the actual file to see if it’s changed.

Additionally, the server hosting your cover art image must allow HTTP HEAD requests.

Warning

Almost no podcatchers support this. iTunes supports it only if you embed the cover in the media file (the same way you would embed an album cover), and recommends that you use Garageband’s Enhanced Podcast feature.

The podcast’s image is used if this isn’t supported.

`is_closed_captioned` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.is_closed_captioned "Permalink to this definition")

Whether this podcast includes a video episode with embedded [closed captioning](https://en.wikipedia.org/wiki/Closed_captioning) support. Defaults to `False`.

| Type: | [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") |
| ----- | ---------------------------------------------------------------------------------- |
| RSS:  | itunes:isClosedCaptioned                                                           |

`link` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.link "Permalink to this definition")

The link to the full version of this episode’s [`summary`](https://podgen.readthedocs.io/en/latest/#podgen.Episode.summary "podgen.Episode.summary"). Remember to start the link with the scheme, e.g. [https://](https://).

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| ----- | ------------------------------------------------------------------------------- |
| RSS:  | link                                                                            |

`long_summary` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.long_summary "Permalink to this definition")

A long (read: full) summary, which supplements the shorter [`summary`](https://podgen.readthedocs.io/en/latest/#podgen.Episode.summary "podgen.Episode.summary"). Like summary, this must be compatible with XHTML parsers; use `podgen.htmlencode()` if this isn’t HTML.

This attribute should be seen as a full, longer variation of summary if summary exists. Even then, the long\_summary should be independent from summary, in that you only need to read one of them. This means you may have to repeat the first sentences.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") which can be parsed as XHTML. |
| ----- | ------------------------------------------------------------------------------------------------------------- |
| RSS:  | content:encoded or description                                                                                |

`media`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.media "Permalink to this definition")

Get or set the [`Media`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media "podgen.Media") object that is attached to this episode.

Note that if [`id`](https://podgen.readthedocs.io/en/latest/#podgen.Episode.id "podgen.Episode.id") is not set, the media’s URL is used as the id. If you rely on this, you should make sure the URL never changes, since changing the id messes up with clients (they will think this episode is new again, even if the user has listened to it already). Therefore, you should only rely on this behaviour if you own the domain which the episodes reside on. If you don’t, then you must set [`id`](https://podgen.readthedocs.io/en/latest/#podgen.Episode.id "podgen.Episode.id") to an appropriate value manually.

| Type: | [`podgen.Media`](https://podgen.readthedocs.io/en/latest/api.media.html#podgen.Media "podgen.Media") |
| ----- | ---------------------------------------------------------------------------------------------------- |
| RSS:  | enclosure and itunes:duration                                                                        |

`position`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.position "Permalink to this definition")

A custom position for this episode on the iTunes store page.

If you would like this episode to appear first, set it to `1`. If you want it second, set it to `2`, and so on. If multiple episodes share the same position, they will be sorted by their [`publication date`](https://podgen.readthedocs.io/en/latest/#podgen.Episode.publication_date "podgen.Episode.publication_date").

To remove the order from the episode, set the position back to [`None`](https://docs.python.org/3/library/constants.html#None "(in Python v3.8)").

| Type: | [`int`](https://docs.python.org/3/library/functions.html#int "(in Python v3.8)") |
| ----- | -------------------------------------------------------------------------------- |
| RSS:  | itunes:order                                                                     |

`publication_date`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.publication_date "Permalink to this definition")

The time and date this episode was first published.

The value can be a [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)"), which will be parsed and made into a [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)") object when assigned. You may also assign a [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)") object directly. In both cases, you must ensure that the value includes timezone information.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") (will be converted to and stored as [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)")) or [`datetime.datetime`](https://docs.python.org/3/library/datetime.html#datetime.datetime "(in Python v3.8)"). |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| RSS:  | pubDate                                                                                                                                                                                                                                                                                                                                          |

Note

Don’t use the media file’s modification date as the publication date, unless they’re the same. It looks very odd when an episode suddenly pops up in the feed, but it claims to be several hours old!

`rss_entry`()[\[source\]](https://podgen.readthedocs.io/en/latest/_modules/podgen/episode.html#Episode.rss_entry)[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.rss_entry "Permalink to this definition")

Create an RSS item using lxml’s etree and return it.

This is primarily used by [`podgen.Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast") when generating the podcast’s RSS feed.

| Returns: | etree.Element(‘item’) |
| -------- | --------------------- |

`subtitle` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.subtitle "Permalink to this definition")

A short subtitle.

This is shown in the Description column in iTunes. The subtitle displays best if it is only a few words long.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| ----- | ------------------------------------------------------------------------------- |
| RSS:  | itunes:subtitle                                                                 |

`summary` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.summary "Permalink to this definition")

The summary of this episode, in a format that can be parsed by XHTML parsers.

If your summary isn’t fit to be parsed as XHTML, you can use `podgen.htmlencode()` to fix the text, like this:

```default
>>> ep.summary = podgen.htmlencode("We spread lots of love <3")
>>> ep.summary
We spread lots of love &lt;3
```

In iTunes, the summary is shown in a separate window that appears when the “circled i” in the Description column is clicked. This field can be up to 4000 characters in length.

See also [`Episode.subtitle`](https://podgen.readthedocs.io/en/latest/#podgen.Episode.subtitle "podgen.Episode.subtitle") and [`Episode.long_summary`](https://podgen.readthedocs.io/en/latest/#podgen.Episode.long_summary "podgen.Episode.long_summary").

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") which can be parsed as XHTML. |
| ----- | ------------------------------------------------------------------------------------------------------------- |
| RSS:  | description                                                                                                   |

`title` *= None*[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.title "Permalink to this definition")

This episode’s human-readable title. Title is mandatory and should not be blank.

| Type: | [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.8)") |
| ----- | ------------------------------------------------------------------------------- |
| RSS:  | title                                                                           |

`withhold_from_itunes`[¶](https://podgen.readthedocs.io/en/latest/#podgen.Episode.withhold_from_itunes "Permalink to this definition")

Prevent this episode from appearing in the iTunes podcast directory. Note that the episode can still be found by inspecting the XML, so it is still public.

One use case would be if you knew that this episode would get you kicked out from iTunes, should it make it there. In such cases, you can set withhold\_from\_itunes to `True` so this episode isn’t published on iTunes, allowing you to publish it to everyone else while keeping your podcast on iTunes.

This attribute defaults to `False`, of course.

| Type: | [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.8)") |
| ----- | ---------------------------------------------------------------------------------- |
| RSS:  | itunes:block                                                                       |

[**AI and large language models (LLMs)** are revolutionizing the way businesses use and process data.](https://server.ethicalads.io/proxy/click/9275/01998bcd-1c2c-7c10-87ba-c6fea4b58f46/)

[Ads by EthicalAds](https://www.ethicalads.io/advertisers/?ref=ea-text)