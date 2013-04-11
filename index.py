#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2, re, urllib, cgi

def getDDDCorpora():
  xml = urllib2.urlopen('https://korpling.german.hu-berlin.de/annis3-service/annis/query/corpora').read().decode("utf-8")
  regex = re.compile("<name>(DDD-.+?)</name>")
  return regex.findall(xml)

def getDDDAnnotations(corpora):
  annodict = {}
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
        annodict[name].extend(values)
        annodict[name] = list(set(annodict[name]))
      except KeyError:
        annodict[name] = list(set(values))
  return annodict

def aql(ps):
  numbers = u""
  statements = u""
  if len(ps) > 1:
    j = 1
    i = 1
    for p in ps:
      statements = statements + p + " &\n"
    while i <= len(ps) and j < ((len(ps) * 2) - 1):
      if j%2 == 1:
        numbers = numbers + "#" + str(i)
        i += 1
      if j%2 == 0:
        numbers = numbers + " .1,3 #" + str(i) + " &\n"
      j += 1
  if len(ps) == 1:
    statements = ps[0]
  return unicode(statements + numbers).strip("&\n").encode("utf-8")

def resolveDiacritics(word):
  word = word.encode("utf-8")
  diacritics = {ur"i": ur"[iî\u0131\u0304\u0306\u0131\u0304\u0131\u0306]",
                ur"u": ur"[uûu\u0304\u0306u\u0304u\u0306]",
                ur"o": ur"[oôo\u0304\u0306o\u0304o\u0306]",
                ur"z": ur"[z\u01B7]",
                ur"s": ur"[sß\u017F]",
                ur"d": ur"[d\u0110\u0111\u00DE\u00FE]",
                ur"e": ur"[eêe\u0304\u0306e\u0304e\u0306\u025B\u03B5]"
               }
  for letter in diacritics.keys():
    word = word.replace(letter, diacritics[letter])
  return word

def parseQuery(d, a):
  try:
    words = d["query"][0].split()
    parameters = []
    for word in words:
      search = ""
      for attr in a.keys():
        worddiacritics = resolveDiacritics(word)
        regex = re.compile(r"\b" + worddiacritics + r"\b", re.UNICODE | re.IGNORECASE)
        searchlist = []
        for annoattr in a[attr]:
          if len(regex.findall( annoattr )) > 0:
            searchlist.append(regexescape(annoattr))
        if len(searchlist) > 0:
          search = attr + "=/(" + "|".join(searchlist) + ")/"
        if search:
          parameters.append(search)
          break
    return aql(parameters)
  except KeyError:
    return ""

def regexescape(s):
  s = s.replace("|", "\|")
  s = s.replace("(", "\(")
  s = s.replace(")", "\)")
  s = s.replace(".", "\.")
  return s

def parseZeit(d, a):
  out = []
  try:
    eras = d["zeit"]
    poseras = a["default_ns:Entstehungszeit"]
    for era in eras:
      for posera in poseras:
        if posera.startswith(era):
          if posera not in out:
            out.append(posera)
    q = unicode("meta::Entstehungszeit=/(" + "|".join(out) + ")/").encode("utf-8")
    return q
  except KeyError:
    return ""

def parseRaum(d, a):
  out = []
  try:
    locs = d["raum"]
    poslocs = a["default_ns:Sprachlandschaft"]
    for loc in locs:
      for posloc in poslocs:
        if posloc.lower().startswith(loc.lower()):
          if posloc not in out:
            out.append(posloc)
    q = unicode("meta::Sprachlandschaft=/(" + "|".join(out) + ")/").encode("utf-8")
    return q
  except KeyError:
    return ""

def parseText(d, a):
  out = []
  try:
    regs = d["text"]
    posregs = a["default_ns:Textbereich"]
    for reg in regs:
      for posreg in posregs:
        if posreg.lower().startswith(reg.lower()):
          if posreg not in out:
            out.append(posreg)
    q = unicode("meta::Textbereich=/(" + "|".join(out) + ")/").encode("utf-8")
    return q
  except KeyError:
    return ""

def createAQL(query, zeit, raum, text):
  baseurl = "https://korpling.german.hu-berlin.de/annis3/instance-ddd#"
  aqlurl = ""
  if query:
    aqlurl = query.strip()
  if text:
    aqlurl = aqlurl + " & " + text.strip()
  if zeit:
    aqlurl = aqlurl + " & " + zeit.strip()
  if raum:
    aqlurl = aqlurl + " & " + raum.strip()
  aqlurl = "_q=" + aqlurl.encode("base64")
  aqlstr = query + text + zeit + raum
  corpora = getDDDCorpora()
  scope = "&_c=" + unicode(",".join(corpora)).encode("base64") + "&cl=5&cr=5&s=0&l=10&seg=txt"
  return aqlstr, unicode(baseurl.strip() + aqlurl + scope.strip())

def cgiFieldStorageToDict( fieldStorage ):
  params = {}
  for key in fieldStorage.keys():
    params[key] = fieldStorage.getlist(key)
#  params = params = {"query": ["lieber"], "text": ["alltag"]}
  return params

def form2aql(form, adict):
  d = cgiFieldStorageToDict(form)
  query = parseQuery(d, adict)
  zeit = parseZeit(d, adict)
  raum = parseRaum(d, adict)
  text = parseText(d, adict)
  return createAQL(query, zeit, raum, text)


corpora = getDDDCorpora()
annos = getDDDAnnotations(corpora)
form = cgi.FieldStorage()
aqlstr, url = form2aql(form, annos)

print "Content-Type: text/html\n"
print '<html><body>'
print '<a href="' + url + '">perform the search in Annis</a>'
print '<pre>Die AQL Abfrage ist: ' + aqlstr + '</pre>'
print '<pre>Die url ist: ' + url + '</pre>'
print '</body></html>'
