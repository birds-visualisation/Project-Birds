import wikipedia
import urllib


def get_bird_info(birdName):
    birdName = birdName.replace("_", " ")
    wikipedia.set_lang("fr")
    wikipage = wikipedia.page(birdName)
    f = filter(lambda url: url[-3:] in ["jpg", "png"], wikipage.images)
    return wikipage.summary, next(f), wikipage.url
