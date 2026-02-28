---
title: "Using PubSubHubbub — PodGen Documentation"
source: "https://podgen.readthedocs.io/en/latest/advanced/pubsubhubbub.html"
author:
published:
created: 2025-09-09
description:
tags:
  - "clippings"
---
PubSubHubbub is a free and open protocol for pushing updates to clients when there’s new content available in the feed, as opposed to the traditional polling clients do.

Read about [what PubSubHubbub is](https://en.wikipedia.org/wiki/PubSubHubbub) before you continue.

Note

While the protocol supports having multiple PubSubHubbub hubs for a single Podcast, there is no support for this in PodGen at the moment.

Warning

Read through the whole guide at least once before you start implementing this. Specifically, you must *not* set the [`pubsubhubbub`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.pubsubhubbub "podgen.Podcast.pubsubhubbub") attribute if you haven’t got a way to notify hubs of new episodes.

---

Contents

- [Using PubSubHubbub](https://podgen.readthedocs.io/en/latest/advanced/#using-pubsubhubbub)
- [Step 1: Set feed\_url](https://podgen.readthedocs.io/en/latest/advanced/#step-1-set-feed-url)
- [Step 2: Decide on a hub](https://podgen.readthedocs.io/en/latest/advanced/#step-2-decide-on-a-hub)
- [Step 3: Set pubsubhubbub](https://podgen.readthedocs.io/en/latest/advanced/#step-3-set-pubsubhubbub)
- [Step 4: Set HTTP Link Header](https://podgen.readthedocs.io/en/latest/advanced/#step-4-set-http-link-header)
- [Step 5: Notify the hub of new episodes](https://podgen.readthedocs.io/en/latest/advanced/#step-5-notify-the-hub-of-new-episodes)

## Step 1: Set feed_url¶

First, you must ensure that the [`Podcast`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast "podgen.Podcast") object has the [`feed_url`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.feed_url "podgen.Podcast.feed_url") attribute set to the URL at which the feed is accessible.

```default
# Assume p is a Podcast object
p.feed_url = "https://example.com/feeds/examplefeed.rss"
```

## Step 2: Decide on a hub¶

The [Wikipedia article](https://en.wikipedia.org/wiki/PubSubHubbub#Usage) mentions a few options you can use (called Community Hosted hub providers). Alternatively, you can set up and host your own server using one of the open source alternatives, like for instance [Switchboard](https://github.com/aaronpk/Switchboard).

## Step 3: Set pubsubhubbub¶

The Podcast must contain information about which hub to use. You do this by setting [`pubsubhubbub`](https://podgen.readthedocs.io/en/latest/api.podcast.html#podgen.Podcast.pubsubhubbub "podgen.Podcast.pubsubhubbub") to the URL which the hub is available at.

```default
p.pubsubhubbub = "https://pubsubhubbub.example.com/"
```

## Step 4: Set HTTP Link Header¶

In addition to embedding the PubSubHubbub hub URL and the feed’s URL in the RSS itself, you should use the [Link header](https://tools.ietf.org/html/rfc5988#page-6) in the HTTP response that is sent with this feed, duplicating the link to the PubSubHubbub and the feed. Example of what it might look like:

```none
Link: <https://link.to.pubsubhubbub.example.org/>; rel="hub",
      <https://example.org/podcast.rss>; rel="self"
```

How you can achieve this varies from framework to framework. Here is an example using [Flask](http://flask.pocoo.org/) (assuming the code is inside a view function):

```default
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

## Step 5: Notify the hub of new episodes¶

Warning

The hub won’t know that you’ve published new episodes unless you tell it about it. If you don’t do this, the hub will assume there is no new content, and clients which trust the hub to inform them of new episodes will think there is no new content either. **Don’t set the pubsubhubbub field if you haven’t set this up yet.**

Different hubs have different ways of notifying it of new episodes. That’s why you must notify the hubs yourself; supporting all hubs is out of scope for PodGen.

If you use the [Google PubSubHubbub](https://pubsubhubbub.appspot.com/) or the [Superfeedr hub](https://pubsubhubbub.superfeedr.com/), there is a pip package called [PubSubHubbub\_Publisher](https://pypi.python.org/pypi/PubSubHubbub_Publisher) which provides this functionality for you. Example:

```default
from pubsubhubbub_publish import publish, PublishError
from podgen import Podcast
# ...
try:
    publish(p.pubsubhubbub, p.feed_url)
except PublishError as e:
    # Handle error
```

In all other cases, you’re encouraged to use [Requests](http://docs.python-requests.org/) to make the necessary [POST request](http://docs.python-requests.org/en/master/user/quickstart/#make-a-request) (if no publisher package is available).

Note

If you have changes in multiple feeds, you can usually send just one single notification to the hub with all the feeds’ URLs included. It is worth researching, as it can save both you and the hub a lot of time.