---
title: "PodGen — PodGen Documentation"
source: "https://podgen.readthedocs.io/en/latest/"
author:
published:
created: 2025-09-09
description:
tags:
  - "clippings"
---
Are you looking for a **clean and simple library** which helps you **generate podcast RSS feeds** from your Python code? Here is how you do that with PodGen:

```default
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

As of March 6th 2020 (v1.1.0), PodGen does not support the additions and changes made by Apple to their podcast standards since 2016, with the exception of the 2019 categories. This includes the ability to mark episodes with episode and season number, and the ability to mark the podcast as “serial”. It is a goal to implement those changes in a new release. Please refer to the [Roadmap](https://podgen.readthedocs.io/en/latest/background/roadmap.html).

## Contents¶

- [Background](https://podgen.readthedocs.io/en/latest/background/index.html)
- [Philosophy](https://podgen.readthedocs.io/en/latest/background/philosophy.html)
- [Scope](https://podgen.readthedocs.io/en/latest/background/scope.html)
- [Why the fork?](https://podgen.readthedocs.io/en/latest/background/fork.html)
- [Inspiration](https://podgen.readthedocs.io/en/latest/background/fork.html#inspiration)
- [Summary of changes](https://podgen.readthedocs.io/en/latest/background/fork.html#summary-of-changes)
- [Roadmap](https://podgen.readthedocs.io/en/latest/background/roadmap.html)
- [License](https://podgen.readthedocs.io/en/latest/background/license.html)
- [Usage Guide](https://podgen.readthedocs.io/en/latest/usage_guide/index.html)
- [Installation](https://podgen.readthedocs.io/en/latest/usage_guide/installation.html)
- [Podcasts](https://podgen.readthedocs.io/en/latest/usage_guide/podcasts.html)
- [Creating a new instance](https://podgen.readthedocs.io/en/latest/usage_guide/podcasts.html#creating-a-new-instance)
- [Mandatory attributes](https://podgen.readthedocs.io/en/latest/usage_guide/podcasts.html#mandatory-attributes)
- [Image](https://podgen.readthedocs.io/en/latest/usage_guide/podcasts.html#image)
- [Optional attributes](https://podgen.readthedocs.io/en/latest/usage_guide/podcasts.html#optional-attributes)
- [Shortcut for filling in data](https://podgen.readthedocs.io/en/latest/usage_guide/podcasts.html#shortcut-for-filling-in-data)
- [Episodes](https://podgen.readthedocs.io/en/latest/usage_guide/episodes.html)
- [Filling with data](https://podgen.readthedocs.io/en/latest/usage_guide/episodes.html#filling-with-data)
- [Shortcut for filling in data](https://podgen.readthedocs.io/en/latest/usage_guide/episodes.html#shortcut-for-filling-in-data)
- [RSS](https://podgen.readthedocs.io/en/latest/usage_guide/rss.html)
- [Full example](https://podgen.readthedocs.io/en/latest/usage_guide/example.html)
- [Advanced Topics](https://podgen.readthedocs.io/en/latest/advanced/index.html)
- [Using PubSubHubbub](https://podgen.readthedocs.io/en/latest/advanced/pubsubhubbub.html)
- [Step 1: Set feed\_url](https://podgen.readthedocs.io/en/latest/advanced/pubsubhubbub.html#step-1-set-feed-url)
- [Step 2: Decide on a hub](https://podgen.readthedocs.io/en/latest/advanced/pubsubhubbub.html#step-2-decide-on-a-hub)
- [Step 3: Set pubsubhubbub](https://podgen.readthedocs.io/en/latest/advanced/pubsubhubbub.html#step-3-set-pubsubhubbub)
- [Step 4: Set HTTP Link Header](https://podgen.readthedocs.io/en/latest/advanced/pubsubhubbub.html#step-4-set-http-link-header)
- [Step 5: Notify the hub of new episodes](https://podgen.readthedocs.io/en/latest/advanced/pubsubhubbub.html#step-5-notify-the-hub-of-new-episodes)
- [Adding new tags](https://podgen.readthedocs.io/en/latest/advanced/extending.html)
- [Quick How-to](https://podgen.readthedocs.io/en/latest/advanced/extending.html#quick-how-to)
- [Example: Adding a ttl element](https://podgen.readthedocs.io/en/latest/advanced/extending.html#example-adding-a-ttl-element)
- [Contributing](https://podgen.readthedocs.io/en/latest/contributing.html)
- [Setting up](https://podgen.readthedocs.io/en/latest/contributing.html#setting-up)
- [Testing](https://podgen.readthedocs.io/en/latest/contributing.html#testing)
- [Values](https://podgen.readthedocs.io/en/latest/contributing.html#values)
- [The Workflow](https://podgen.readthedocs.io/en/latest/contributing.html#the-workflow)
- [API Documentation](https://podgen.readthedocs.io/en/latest/api.html)

## External Resources¶

- [Changelog](https://github.com/tobinus/python-podgen/blob/master/CHANGELOG.md)
- [GitHub Repository](https://github.com/tobinus/python-podgen/tree/master)
- [Python Package Index](https://pypi.org/project/podgen/)