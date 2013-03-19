#!/usr/bin/env python

import urllib2, re, urllib

def getDDDCorpora():
  xml = urllib2.urlopen('https://korpling.german.hu-berlin.de/annis3-service/annis/query/corpora').read().decode("utf-8")
  regex = re.compile("<name>(DDD.+?)</name>")
  return regex.findall(xml)

def getDDDAnnotations(corpora):
  annos = {}
  for corpus in corpora:
    url = str("https://korpling.german.hu-berlin.de/annis3-service/annis/query/corpora/" + corpus + "/annotations?fetchvalues=true")
    xml = urllib2.urlopen(url).read().decode("utf-8")
    regexAttr = re.compile("<annisAttribute>(.+?)</annisAttribute>", re.DOTALL)
    regexAttrName = re.compile("<name>(.+?)</name>")
    regexValues = re.compile("<value>(.+?)</value>")
    attributes = regexAttr.findall(xml)
    for attribute in attributes:
      name = regexAttrName.findall(attribute)[0]
      values = regexValues.findall(attribute)
      try:
        annos[name].extend(values)
        annos[name] = set(annos[name])
      except KeyError:
        annos[name] = values
  return annos

def aql(ps):
  numbers = ""
  statements = ""
  i = 1
  for p in ps:
    statements = statements + p + " &\n"
    numbers = numbers + " #" + str(i) + " .1,3"
    i = i + 1
  return statements + numbers.strip(".1,3")

def parseQuery(d):
  corpora = getDDDCorpora()
  annos = getDDDAnnotations(corpora)
  try:
    words = d["query"][0].split()
    parameters = []
    for word in words:
      word = word.decode("utf-8")
      search = u""
      for attr in annos.keys():
	if word in annos[attr]:
          search = attr + "=\"" + word + "\""
          break
      parameters.append(search)
    return aql(parameters)
  except KeyError:
    return ""

def parseZeit(d):
  try:
    eras = str(d["zeit"])
    return eras
  except KeyError:
    return ""

def parseRaum(d):
  try:
    locs = str(d["raum"])
    return locs
  except KeyError:
    return ""

def parseText(d):
  try:
    regs = str(d["text"])
    return regs
  except KeyError:
    return ""

def createAQL(query, zeit, raum, text):
  baseurl = "https://korpling.german.hu-berlin.de/annis3/Cite/AQL"
  aql = "(" + urllib.quote(query + " " + zeit + " " + raum + " " + text) + ")"
  corpora = getDDDCorpora()
  scope = ",CIDS(" + ",".join(corpora) + "),CLEFT(5),CRIGHT(5)"
  return unicode(baseurl + aql + scope)

def cgiFieldStorageToDict( fieldStorage ):
  params = {}
  for key in fieldStorage.keys():
    params[key] = fieldStorage.getlist(key)
  return params

def form2aql(form):
  d = cgiFieldStorageToDict(form)
  query = parseQuery(d)
  zeit = parseZeit(d)
  raum = parseRaum(d)
  text = parseText(d)
  return createAQL(query, zeit, raum, text)

import cgi
form = cgi.FieldStorage()
aql = form2aql(form)

print "Content-Type: text/html\n"
print '<html><body>'
print aql
print '</body></html>'
