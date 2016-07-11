#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Information template production

first mapping file generation could be separated (and if so also knav stuff)

A known assumption is that in avbildad_namn any string containing exactly
one comma is a person, and any others are assumed to be ships.

@todo: Make this extend some base makeInfo class
@todo: Deprecate/merge test() into run()
"""
import batchupload.helpers as helpers
import batchupload.listscraper as listscraper
import batchupload.csv_methods as csv_methods
import codecs
import json
import os

CWD_PATH = ''
OUT_PATH = u'connections'
BATCH_CAT = u'Media contributed by SMM'  # stem for maintenance categories
BATCH_DATE = u'2015-09'  # branch for this particular batch upload
headerCheck = u'Identifikationsnr|Typ av objekt|Benämning|Material|' + \
              u'Namn-Konstnär|KulturNav|Namn-Konstruktör|KulturNav|' + \
              u'Namn-Konstruktör|Namn-Fotograf|Namn-Tillverkare|' + \
              u'Namn-Tillverkare|Namn-Tillverkare|Datering-Fotografering|' + \
              u'Datering-Produktion|Avbildade namn|KulturNav|' + \
              u'Avbildade namn|Avbildade namn|Avbildade - orter|' + \
              u'Ämnesord|Beskrivning|Motiv-ämnesord|Motiv-beskrivning|' + \
              u'Rättigheter|Samling|Dimukode'

# black-listed
badNamn = (u'okänd fotograf', u'okänd konstnär')
badDate = (u'odaterad', )

# list which needs to be accessible always
kNavList = {}
mappings = {}


def setCWD(filename):
    """
    set CWD_PATH based on infile
    """
    global CWD_PATH
    CWD_PATH = os.path.split(filename)[0]


def test(infile):
    setCWD(infile)
    d = csvToDict(infile)
    loadMappings()
    outdata = {}
    filenames = {}
    for k, v in d.iteritems():
        info = makeInfoTemplate(v)
        filename = generateFilename(v)
        metaCats = getMetaCats(v)
        cats = getContentCat(v, withBenamning=True)
        outdata[getFilenameId(v)] = {u'info': info, u'filename': filename,
                                     u'cats': cats, u'metaCats': metaCats}
        filenames[v['idno']] = filename

    # store filenames
    outFile = u'%s.filenames.txt' % infile
    out = codecs.open(outFile, 'w', 'utf-8')
    for k, v in filenames.iteritems():
        out.write(u'%s\t%s\n' % (k, v))
    out.close()
    print u'Created %s' % outFile

    # store output
    outFile = u'%s.json' % infile
    out = codecs.open(outFile, 'w', 'utf-8')
    out.write(json.dumps(outdata, indent=4, ensure_ascii=False))
    out.close()
    print u'Created %s' % outFile


def run(infile):
    """
    Construct the Information pages for commons
    """
    # load infile
    setCWD(infile)
    d = csvToDict(infile)
    # load mapping files
    loadMappings(update=False)
    info = {}
    for k, v in d.iteritems():
        # check type and determine which info maker
        descr = makeInfoTemplate(v)
        # make categories
        info[k] = {'descr': descr,
                   'contentCat': [],  # must have at least one
                   'otherCat': []}  # don't count towards category number
    # output as json
    pass


def csvToDict(filename, keyColumn=0, codec='utf-8'):
    """

    Cannot use helpers.csvToDict as keys are not unique
    """
    header, lines = csv_methods.open_csv_file(filename, codec=codec)
    if header != headerCheck:
        print 'Header not same as comparison string!'
        exit()

    # populate dictionary
    d = {}
    for l in lines:
        idno = l.split('|')[keyColumn]
        d[idno] = handleLine(l.strip())

    return d


def handleLine(line):
    """
    Parse an individual line into a dict and add kNav matches to kNavList
    return dict
    """
    p = line.split('|')
    d = {}
    d['idno'] = p[0].strip()
    d['typ'] = p[1].strip()
    d['benamning'] = p[2].strip()
    d['material'] = p[3].strip().split(',')
    d['namn_konstnar'] = helpers.flipName(p[4].strip())
    namn_konstnar_knav = p[5].strip()
    d['namn_konstruktor'] = []
    d['namn_konstruktor'].append(helpers.flipName(p[6].strip()))
    namn_konstruktor_knav = p[7].strip()
    d['namn_konstruktor'].append(helpers.flipName(p[8].strip()))
    d['namn_fotograf'] = helpers.flipName(p[9].strip())
    d['namn_tillverkare'] = []
    d['namn_tillverkare'].append(helpers.flipName(p[10].strip()))
    d['namn_tillverkare'].append(helpers.flipName(p[11].strip()))
    d['namn_tillverkare'].append(helpers.flipName(p[12].strip()))
    d['date_foto'] = p[13].strip()
    d['date_produktion'] = p[14].strip()
    d['avbildad_namn'] = []
    d['avbildad_namn'].append(p[15].strip())
    avbildad_namn_knav = p[16].strip()
    d['avbildad_namn'].append(p[17].strip())
    d['avbildad_namn'].append(p[18].strip())
    d['avbildad_ort'] = p[19].strip()
    d['amnesord'] = p[20].strip().split(',')
    d['beskrivning'] = p[21].strip()
    d['motiv_amnesord'] = p[22].strip().split(',')
    d['motiv_beskrivning'] = p[23].strip()
    d['rattighet'] = p[24].strip()
    d['samling'] = p[25].strip()
    d['dimukod'] = p[26].strip()

    # kNav
    if len(namn_konstnar_knav) > 0:
        addTokNavList(namn_konstnar_knav, d['namn_konstnar'])
    if len(avbildad_namn_knav) > 0:
        addTokNavList(avbildad_namn_knav,
                      helpers.flipName(d['avbildad_namn'][0]))
    if len(namn_konstruktor_knav) > 0:
        addTokNavList(avbildad_namn_knav,
                      helpers.flipName(d['namn_konstruktor'][0]))

    # split avbildad_namn into people and ships/boat types
    # a person is anyone with a name like Last, First
    d['avbildad_person'] = []
    d['avbildat_fartyg'] = []
    for a in d['avbildad_namn']:
        if a != helpers.flipName(a):
            d['avbildad_person'].append(helpers.flipName(a))
        else:
            d['avbildat_fartyg'].append(a)
    # overwrite with flipped names
    d['avbildad_namn'] = d['avbildad_person'] + d['avbildat_fartyg']

    # cleanup lists
    d['material'] = helpers.trimList(d['material'])
    d['namn_tillverkare'] = helpers.trimList(d['namn_tillverkare'])
    d['avbildad_person'] = helpers.trimList(d['avbildad_person'])
    d['avbildat_fartyg'] = helpers.trimList(d['avbildat_fartyg'])
    d['avbildad_namn'] = helpers.trimList(d['avbildad_namn'])
    d['namn_konstruktor'] = helpers.trimList(d['namn_konstruktor'])
    d['amnesord'] = helpers.trimList(d['amnesord'])
    d['motiv_amnesord'] = helpers.trimList(d['motiv_amnesord'])

    # cleanup blacklisted
    if d['date_foto'].strip('.').lower() in badDate:
        d['date_foto'] = ''
    if d['date_produktion'].strip('.').lower() in badDate:
        d['date_produktion'] = ''
    if d['namn_konstnar'].lower() in badNamn:
        d['namn_konstnar'] = ''
    if d['namn_fotograf'].lower() in badNamn:
        d['namn_fotograf'] = ''

    return d


def addTokNavList(uuid, namn):
    """
    Add an uuid to kNavList
    """
    # Convert url to uuid
    if uuid.startswith(u'http://kulturnav.org'):
        uuid = uuid.split('/')[-1]
    if len(uuid) > 0:
        if uuid in kNavList.keys():
            if namn not in kNavList[uuid]['namn']:
                kNavList[uuid]['namn'].append(namn)
        else:
            kNavList[uuid] = {'namn': [namn, ]}


def generateFilename(item):
    """
    Given an item (dict) generate an appropriate filename of the shape
    descr - Collection - id
    does not include fieltype
    """
    descr = generateFilenameDescr(item)
    collection = item['samling']
    idno = helpers.cleanString(item['idno'])
    filename = u'%s - %s - %s' % (descr, collection, idno)
    return filename.replace(' ', '_')


def generateFilenameDescr(item):
    """
    Given an item (dict) generate an appropriate description for the filename
    """
    # benamning which need more info
    need_more = (u'Fartygsmodell', u'Fartygsporträtt', u'Marinmotiv',
                 u'Modell', u'Ritning', u'Teckning', u'Akvarell', u'Karta',
                 u'Kopparstick', u'Lavering', u'Sjökort', u'Sjöstrid',
                 u'Porträtt')
    txt = u''
    if item['typ'] == u'Foto':
        if len(item['avbildad_namn']) > 0:
            txt += ', '.join(item['avbildad_namn'])
            if len(item['avbildad_ort']) > 0:
                txt += u'. %s' % item['avbildad_ort']
            if len(item['date_foto']) > 0:
                txt += u'. %s' % item['date_foto']
        elif len(item['motiv_beskrivning']) > 0:
            txt += item['motiv_beskrivning']
    if item['typ'] == u'Föremål':
        txt += item['benamning']
        if item['benamning'] in need_more:
            txt2 = ''
            if len(item['avbildad_namn']) > 0:
                txt2 += ', '.join(item['avbildad_namn'])
            elif len(item['motiv_beskrivning']) > 0:
                txt2 += item['motiv_beskrivning']
            if len(item['avbildad_ort']) > 0:
                txt2 += u'. %s' % item['avbildad_ort']
            if len(item['date_produktion']) > 0:
                txt2 += u'. %s' % item['date_produktion']
            txt = u'%s-%s' % (txt, txt2)
    txt = helpers.cleanString(txt)
    txt = helpers.touchup(txt)
    return helpers.shortenString(txt)


def getFilenameId(item):
    """
    Convert the idno to the equivalent format used for the image files
    """
    return item['idno'].replace(u':', u'_').replace(u'/', u'_')


def getSourceCat(item):
    if item['samling'] == u'Sjöhistoriska museet':
        return u'Images from Sjöhistoriska museet‎'
    elif item['samling'] == u'Vasamuseet':
        return u'Images from Vasamuseet'
    else:
        print u'No Institution-catalog'


def getContentCat(item, withBenamning=False):
    """
    Extract any mapped keyword categories or depicted categories
    """
    cats = []
    keywords = item['amnesord'] + item['motiv_amnesord']
    if withBenamning and item['benamning']:
        keywords += [item['benamning'], ]
    for k in keywords:
        if k.lower() in mappings['keywords']:
            cats += mappings['keywords'][k.lower()]['category']
    # depicted objects
    for k in item['avbildad_namn']:
        if k in mappings['people']:
            cats += mappings['people'][k]['category']
    # depicted places?

    cats = list(set(cats))  # remove any duplicates
    return cats


def getMetaCats(item):
    """
    Set meta categories
    """
    cats = []

    # base cats
    cats.append(getSourceCat(item))
    cats.append(u'%s: %s' % (BATCH_CAT, BATCH_DATE))

    # problem cats
    if not getContentCat(item):  # excludes benamning
        cats.append(u'%s: improve categories' % BATCH_CAT)
    if not getDescription(item):
        cats.append(u'%s: add description' % BATCH_CAT)

    # creator cats
    creators = item['namn_tillverkare'] + item['namn_konstruktor']
    creators.append(item[u'namn_konstnar'])
    creators.append(item[u'namn_fotograf'])
    for creator in creators:
        if creator and creator in mappings['people'] and \
                mappings['people'][creator]['category']:
            cats += mappings['people'][creator]['category']

    cats = list(set(cats))  # remove any duplicates
    return cats


def getInstitution(item):
    if item['samling'] == u'Sjöhistoriska museet':
        return u'{{Institution:Sjöhistoriska museet}}'
    elif item['samling'] == u'Vasamuseet':
        return u'{{Institution:Vasamuseet}}'
    else:
        print u'No Institution'


def getLicense(item):
    """
    Sets rights and attribution and runs a minor sanity check
    note: cannot determine death year of creator
    """
    if item['rattighet'] == u'Erkännande-Dela lika':
        return u'{{CC-BY-SA-3.0|%s}}' % getSource(item)
    elif item['rattighet'] == u'Utgången skyddstid':
        if item['typ'] == u'Foto':
            if len(item['date_foto']) > 0 and \
                    int(item['date_foto'][:4]) > 1969:
                print '%s: PD-Sweden-photo with year > 1969' % item['idno']
            return u'{{PD-Sweden-photo}}'
        elif item['typ'] == u'Föremål':
            testdate = item['date_produktion'].lower().strip('ca efter')
            if len(item['date_produktion']) > 0 and int(testdate[:4]) > 1945:
                print '%s: PD-old-70 with year > 1945' % item['idno']
            return u'{{PD-old-70}}'


def getDate(date):
    """
    Local logic for identifying ranges then sending each part to
    helpers.stdDate
    """
    # is this a range?
    dates = date.split(' - ')
    if len(dates) == 2:
        d1 = helpers.stdDate(dates[0])
        d2 = helpers.stdDate(dates[1])
        if d1 is not None and d2 is not None:
            if d1 == d2:
                return d1
            else:
                return u'{{other date|-|%s|%s}}' % (d1, d2)
    else:
        d = helpers.stdDate(date)
        if d is not None:
            return d
    # if you get here you have failed
    print u'Unhandled date: %s' % date


def getDepictedPlace(item):
    """
    given an item get a linked version of the depicted Place
    """
    place = item['avbildad_ort']
    if place in mappings['places']:
        if mappings['places'][place]['other']:
            return mappings['places'][place]['other']

    return item['avbildad_ort']


def getDepictedObject(item, typ):
    """
    given an item get a linked version of the depicted person/ship
    param typ: one of "person", "ship", "all"
    """
    # determine type
    label = None
    if typ == 'person':
        label = 'avbildad_person'
    elif typ == 'ship':
        label = 'avbildat_fartyg'
    elif typ == 'all':
        label = 'avbildad_namn'
    else:
        print u'getDepictedObject() called with invalid type'
        return

    # extract links
    linkedObjects = []
    for obj in item[label]:
        if obj in mappings['people']:
            if mappings['people'][obj]['link']:
                linkedObjects.append(
                    u'[[%s|%s]]' % (mappings['people'][obj]['link'], obj))
            elif mappings['people'][obj]['category']:
                if len(mappings['people'][obj]['category']) != 0:
                    print u'Object linking with multiple categoires: ' \
                          u'%s (%s)' % (obj, ', '.join(
                                        mappings['people'][obj]['category']))
                    linkedObjects.append(obj)
                else:
                    linkedObjects.append(
                        u'[[:Category:%s|%s]]' % (
                            mappings['people'][obj]['category'][0], obj))
            elif mappings['people'][obj]['more']:  # kulturnav
                linkedObjects.append(
                    u'[%s %s]' % (mappings['people'][obj]['more'], obj))
            else:
                linkedObjects.append(obj)
        else:
            linkedObjects.append(obj)
    return linkedObjects


def getCreator(creator):
    """
    given a creator (or creators) return the creator template,
    linked entry or plain name
    """
    # multiple people
    if isinstance(creator, list):
        creators = []
        for person in creator:
            creators.append(getCreator(person))
        return '</br>'.join(creators)
    # single person with fallback chain creator, link, category, extlink
    if creator in mappings['people']:
        if mappings['people'][creator]['creator']:
            return u'{{Creator:%s}}' % mappings['people'][creator]['creator']
        elif mappings['people'][creator]['link']:
            return u'[[%s|%s]]' % (mappings['people'][creator]['link'],
                                   creator)
        elif mappings['people'][creator]['category']:
            return u'[[:Category:%s|%s]]' % (
                mappings['people'][creator]['category'][0], creator)
        elif mappings['people'][creator]['more']:  # kulturnav
            return u'[%s %s]' % (mappings['people'][creator]['more'], creator)
    # if you get here you have failed to match
    return creator


def getMaterials(item):
    """
    given an item get a linked version of the materials
    """
    linkedMaterials = []
    for material in item['material']:
        material = material.lower()
        if material in mappings['materials'] and \
                mappings['materials'][material]['technique']:
            linkedMaterials.append(
                u'{{technique|%s}}' %
                mappings['materials'][material]['technique'])
        else:
            linkedMaterials.append(material)
    return ', '.join(linkedMaterials)


def getIDLink(item):
    """
    Format an accession number link
    """
    dimuUrl = u'//digitaltmuseum.se/%s' % item['dimukod']
    return u'[%s %s]' % (dimuUrl, item['idno'])


def getSource(item):
    """
    Given an item produce a source statement
    """
    if item['namn_fotograf']:
        return u'%s / %s' % (item['namn_fotograf'], item['samling'])
    else:
        return item['samling']


def getDescription(item):
    """
    Given an item get an appropriate description
    """
    descr = ''
    if item['benamning']:
        descr += u'%s: ' % item['benamning']
    if item['motiv_beskrivning']:
        descr += u'%s. ' % item['motiv_beskrivning']
    if item['beskrivning']:
        descr += u'%s. ' % item['beskrivning']

    if len(descr) > 0:
        descr = u'{{sv|%s}}' % descr.rstrip(' :')
    return descr


def getOriginalDescription(item):
    """
    Given an item get an appropriate original description
    """
    descr = ''
    if item['benamning']:
        descr += u'\n%s: %s\n' % (helpers.italicize(u'Benämning'),
                                  item['benamning'])
    if item['motiv_beskrivning']:
        descr += u'\n%s: %s\n' % (helpers.italicize(u'Motivbeskrivning'),
                                  item['motiv_beskrivning'])
    if item['motiv_amnesord']:
        descr += u'\n%s: %s\n' % (helpers.italicize(u'Motiv-ämnesord'),
                                  ', '.join(item['motiv_amnesord']))
    if item['beskrivning']:
        descr += u'\n%s: %s\n' % (helpers.italicize(u'Beskrivning'),
                                  item['beskrivning'])
    if item['amnesord']:
        descr += u'\n%s: %s\n' % (helpers.italicize(u'Ämnesord'),
                                  ', '.join(item['amnesord']))
    return descr


def makeInfoTemplate(item):
    """
    given an item of any type return the filled out template
    """
    if item['typ'] == u'Foto':
        return makeFotoInfo(item)
    elif item['typ'] == u'Föremål':
        return makeArtworkInfo(item)


def makeFotoInfo(item):
    """
    given an item of typ=Foto output the filled out template
    """
    descr = u'{{Photograph\n'
    descr += u' |photographer         = %s\n' % getCreator(
        item['namn_fotograf'])
    descr += u' |title                = \n'
    descr += u' |description          = %s\n' % getDescription(item)
    descr += u' |original description = %s\n' % getOriginalDescription(item)
    descr += u' |depicted people      = %s\n' % '/'.join(
        getDepictedObject(item, typ='person'))
    descr += u' |depicted place       = %s\n' % getDepictedPlace(item)
    if item['avbildat_fartyg']:
        linkedObjects = getDepictedObject(item, typ='ship')
        descr += u' |other_fields_2       = {{depicted ship' \
                 u'|style=information field|%s}}\n' % '|'.join(linkedObjects)
    descr += u' |date                 = %s\n' % getDate(item['date_foto'])
    descr += u' |medium               = %s\n' % getMaterials(item)
    descr += u' |institution          = %s\n' % getInstitution(item)
    descr += u' |accession number     = %s\n' % getIDLink(item)
    descr += u' |source               = %s\n' % getSource(item)
    descr += u' |permission           = {{SMM cooperation project}}\n'
    descr += u'%s\n' % getLicense(item)
    descr += u' |other_versions       = \n'
    descr += u'}}'
    return descr


def makeArtworkInfo(item):
    """
    given an item of typ=Föremål output the filled out template
    """
    descr = u'{{Artwork\n'
    descr += u' |artist               = '
    if item['namn_konstnar']:
        descr += getCreator(item['namn_konstnar'])
    elif item['namn_konstruktor']:
        descr += getCreator(item['namn_konstruktor'])
    descr += u'\n'
    if item['namn_tillverkare']:
        descr += u' |other_fields_1       = {{Information field' \
                 u'|name={{LSH artwork/i18n|manufacturer}}' \
                 u'|value=%s}}\n' % getCreator(item['namn_tillverkare'])
    descr += u' |title                = \n'
    descr += u' |object type          = %s\n' % item['benamning']
    descr += u' |description          = %s' % getDescription(item)
    if item['avbildad_person']:
        linkedObjects = getDepictedObject(item, typ='person')
        descr += u'<br>\n{{depicted person|style=plain text|%s}}' % \
                 '|'.join(linkedObjects)
    if item['avbildat_fartyg']:
        linkedObjects = getDepictedObject(item, typ='ship')
        descr += u'<br>\n{{depicted ship|style=plain text|%s}}' % \
                 '|'.join(linkedObjects)
    if item['avbildad_ort']:
        descr += u'<br>\n{{depicted place|%s}}' % getDepictedPlace(item)
    descr += u'\n'
    descr += u' |other_fields_2       = {{Information field' \
             u'|name={{original caption/i18n|header}}' \
             u'|value=%s}}\n' % getOriginalDescription(item)
    descr += u' |date                 = %s\n' % getDate(
        item['date_produktion'])
    descr += u' |medium               = %s\n' % getMaterials(item)
    descr += u' |institution          = %s\n' % getInstitution(item)
    descr += u' |accession number     = %s\n' % getIDLink(item)
    descr += u' |source               = %s\n' % getSource(item)
    descr += u' |permission           = {{SMM cooperation project}}\n'
    descr += u'%s\n' % getLicense(item)
    descr += u' |other_versions       = \n'
    descr += u'}}'
    return descr


def loadMappings(update=True):
    """
    update mapping files, load these and package appropriately
    param update: whether download the latest mappings
    """
    # update mappings
    pages = {'people': 'people', 'keywords': 'keywords',
             'places': 'places', 'materials': 'materials'}
    if update:
        commons_prefix = u'Commons:Statens maritima museer/Batch upload'
        listscraper.scrape(pages, commons_prefix, working_path=CWD_PATH,
                           out_path=OUT_PATH)

    # read mappings
    for k, v in pages.iteritems():
        listfile = os.path.join(CWD_PATH, OUT_PATH, u'commons-%s.json' % v)
        f = codecs.open(listfile, 'r', 'utf8')
        pages[k] = json.load(f)
        f.close()

    # package mappings for consumption
    people = {}
    for p in pages['people']:
        if isinstance(p['more'], list):
            p['more'] = '/'.join(p['more'])  # since this should be an url
        people[p['name']] = listscraper.formatEntry(p)
    keywords = {}
    for p in pages['keywords']:
        keywords[p['name']] = listscraper.formatEntry(p)
    places = {}
    for p in pages['places']:
        places[p['name']] = listscraper.formatEntry(p)
    materials = {}
    for p in pages['materials']:
        materials[p['name']] = listscraper.formatEntry(p)

    # add to mappings
    mappings['people'] = people
    mappings['keywords'] = keywords
    mappings['places'] = places
    mappings['materials'] = materials


if __name__ == "__main__":
    import sys
    usage = '''Usage: python makeInfo.py infile'''
    argv = sys.argv[1:]
    if len(argv) == 1:
        test(argv[0])
    else:
        print usage
# EoF
