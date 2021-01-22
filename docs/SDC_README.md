# SDC in-data format

## Main structure

The in-data is expected as a json-like dictionary entry where the main keys are
`edit_summary`, `caption` and the *Pid*s of any claims that are added.

Short example:
```json
{
    "edit_summary": "Uploading SDC data for newly uploaded image",
    "caption": {
        "en": "The Lund underground in moonlight.",
        "sv": "Lunds tunnelbana i månsken."
    },
    "P170": "Q123",
    "P180": "57"
}
```

For a more extensive example suited for test-upload to [Beta Commons](https://commons.wikimedia.beta.wmflabs.org/)
see [docs/SDC_beta_commons_demo.sdc](docs/SDC_beta_commons_demo.sdc).

### edit_summary

The `edit_summary` field is a simple text field used to provide an edit summary
when the data is uploaded. You can use `{count}` in the string to include the
number of statements added. This field is overridden if an edit_summary is passed
directly to `upload_single_sdc_data()`. If no edit summary is provided the
default one below is used:

`'Added {count} structured data statement(s) to recent upload'`

### caption

The `caption` field takes the form of a simple dictionary where the keys are the
[language codes](https://www.wikidata.org/wiki/Help:Wikimedia_language_codes/lists/all)
and the values are plain text strings. This data is used to set the *caption*
(*label* in Wikibase lingo) of the file.

### Pid claims

Pid/Property claims can be provided in up to three formats depending on the data
type of the property and if any qualifiers are provided.

The *simple claim format* can be used for any data type which can be provided as
a simple string and where the claim has no qualifiers or a *prominent* flag
(see *complex claim format* below).

`"Pid": "<string_value>`

The *complex claim format* can be used for any data type and additionally supports
qualifiers and and marking the claim as *prominent*.
```python
"Pid": {
    "_": <value>,
    "prominent": <bool>,
    "qualifier Pid_1": <qualifier_claim>,
    … more qualifiers
}
```

The format of `<value>` will depend on the data type. See the [Data type formats](#data-type-formats)
section below.

`prominent` is provided with a boolean value. If the key is not provided the *False*
is assumed. Setting the key to `True` sets the *prominent* flag on the claim
(*preferred* rank in Wikibase lingo).

The qualifier `<qualifier_claim>` supports the same three formats as the main claim
with the difference that the *complex claim format* does not support qualifiers
or the *prominent* flag and that the `<value>` can be provided either directly or
under the `_` key.

The *list claim format* can be used to supply multiple claims for the same Pid.
Both the simple and the complex claim formats are supported.
```python
"Pid": [
    "<string_value>",
    {
        "_": <value>,
        "prominent": <bool>
    }
]
```

Note that even when the `<value>` is numeric it must be provided as a string.

Any keys provided other than the ones described above (on the main level or
inside claims) are ignored.

## Data type formats

How a value is interpreted is based on the Property for which it is provided, the
expected data type is loaded from the underlying Wikibase installation itself.

This tool does not do any data validation so if you pass it rubbish which sort of
looks right you'll hopefully get complaints from pywikibot or the MediaWiki API.

### Simple string values

Many data types simply consist of a string value. This includes:
external identifiers, urls, math notation, musical notation and strings.

Examples:
*   String: `"Some text"`
*   Url: `"https://commons.wikimedia.org"`
*   Math: `"E = m c^2"`
*   Musical notation: `"\relative c' { c d e f | g2 g | a4 a a a | g1 |}"`
*   External identifier: `"123-345"`

Additionally [items](#items), [Commons media](#commons-media), unitless [quantities](#quantity),
[tabular data](#tabular-data-geo-shapes) and [geo shapes](#tabular-data-geo-shapes)
can be supplied as simple strings here. The assumptions made for this convenience
are described in the relevant sections below.

### Items

For this data types the [Qid](https://www.wikidata.org/wiki/Wikidata:Glossary#QID)
of the item is supplied as a simple string. The site on which the item is expected
is determined by the Wikibase installation. So on e.g. when adding structured data
to [Beta Commons](https://commons.wikimedia.beta.wmflabs.org/) the Qid is expected
on [Beta Wikidata](https://wikidata.beta.wmflabs.org/wiki/).

Example: `"Q42"`

### Commons media

For this data type the page name is supplied as a simple string. The "File:" namespace
prefix of the page name is optional. The data page will always be expected to live
Wikimedia Commons, independently on which wiki your are writing structured data to.

Example values: `"File:Exempel_WIKI.jpg"` or `"Exempel_WIKI.jpg"`.

### Tabular data / Geo shapes

For these two data types the page name is supplied as a simple string. The "Data:"
namespace prefix of the page name must be included. The site on which the pages must
live is determined by the Wikibase installation.

Note e.g. that for statements added to Beta Commons the Data pages are still expected
to live on "normal" Wikimedia Commons.

Example values: `"Data:DateI18n.tab"` or `"Data:Sweden.map"`.

### Point in time / Date

A date can be provided either using an ISO_8601 string or a timestamp string. In
either case the largest precision that will be used is that of a day (due to Wikidata's
settings) so "2020-12-31" and "2020-12-31T23:59:59Z" will result in the same output.

Example values:
*   Fully qualified date: `"2020-12-31"` or `"2020-12-31T23:59:59Z"`
*   Year adnd month only: `2020-12`
*   Year only: `2020`

### Monolingual text

Monolingual text requires the value be supplied as a dictionary with the keys
`text` (a plain text string) and `lang` is the [language code](https://www.wikidata.org/wiki/Help:Monolingual_text_languages).

Example values:
```json
{
    "text": "Spider",
    "lang": "en"
}
```
```json
{
    "text": "Hämppi",
    "lang": "fit"
}
```

### Quantity

Quantities can either be supplied with or without units. If no unit is to be used
then the value must be supplied as a plain string using "." as a decimal sign.

Example: `"123.4"`

If the quantity comes with a unit then it most be provided as a dictionary with
the `value` and `unit` keys. The value of `unit` should be the Qid corresponding
to the unit on the used Wikibase installation.

Example (using [kg](https://www.wikidata.org/wiki/Q11570) as the unit):
```json
{
    "value": "123.4",
    "unit": "Q11570"
}
```

### Coordinates

Coordinates are supplied as as a dictionary with `lat` and `lon` keys where the
longitude and latitude values are provided as strings in decimal format.  
Example:
```json
{
    "lat": "55.708333",
    "lon": "13.199167"
}
```

Note that the number of significant figures provided is used to determine the
precision of the coordinate. So `{"lat": "55.7", "lon": "13.2"}` will be interpreted
differently from `{"lat": "55.70", "lon": "13.2"}`.
