from lxml import etree as ET
import re
import string
import spacy # need to be installed/downloaded
import os

script_dir = os.path.dirname(__file__) #absolute directory the script is in

nlp = spacy.load("de_core_news_lg") # need to be installed/downloaded

dramas = ["goethe-goetz-von-berlichingen-mit-der-eisernen-hand", "lessing-emilia-galotti", "schiller-maria-stuart", "goethe-iphigenie-auf-tauris","schlegel-canut", "lenz-der-hofmeister", "schiller-die-raeuber", "gellert-die-zaertlichen-schwestern", "goethe-die-natürliche-tochter",""]

dir_path = "unannotated-texts"
abs_file_path = os.path.join(script_dir, dir_path)
abs_file_path = os.path.normpath(abs_file_path)

directory = os.fsencode(abs_file_path)
    


#regular expressions for detecting entrances
entrances1 = re.compile(r'((((\btritt\b|\btreten\b).{,20}(\bherein\b|\bauf\b|\bvor\b|\bzu\b|\bein\b|\bhervor\b)))|(((\bherein|\bauf|\bvor|\bzu|\bein|\bhervor).{,20}(tritt\b|treten\b))))')
entrances2 = re.compile(r'\bkommend\b|\beintretend\b|\bhereinstürzend\b')
entrances3 = re.compile(r'\baus\b.{,20}\btritt\b|\btritt\b.{,20}\baus\b') 

entrances4 = re.compile(r'\bgesprungen\b|\bk(o|ö)mm(en|t)\b|\bgelaufen\b|\bgeführt\b')
entrances5 = re.compile(r'\bbetr(eten|itt)\b')
entrances6 = re.compile(r'\bnah(en|t)\b')

entrances7 = re.compile(r'((((\bstürz.{,3}\b).*(\bherein\b|\bauf\b|\bhervor\b)))|(((\bherein|\bauf|\bhervor).{,20}(stürz.{,3}\b))))') #stürzen oder stürzet oder stürzend oder stürzt oder ...

#regular expressions for detecting exits
exit1 = re.compile(r'(\bab\b|\bherein\b|\bin(s)?\b|\bhinein\b|\bhinaus\b).{,20}\bgeh(t|en|n)\b|\bgeh(t|en|n)\b.{,20}(\bab\b|\bherein\b|\bin(s)?\b|\bhinein\b|\bhinaus\b)|\babgeh(t|en|n)\b')
exit2 = re.compile(r'(\bfort\b|\bvorbei\b|\bhinaus\b)')
exit3 = re.compile(r'\bführt\b.{,20}\bab\b|\bab.{,20}führt\b')
exit4 = re.compile(r'\bstürzt\b.{,20}\bin\b|\bin\b.{,20}\bstürzt\b')

exit5 = re.compile(r'(\bentfern.*\b).{,20}\bsich\b|\bsich\b.{,20}(\bentfern.*\b)')
exit6 = re.compile(r'^.*(?<!\bauf\b \bund\b )\bab\b(\.)?$') #"ab" but not "auf und ab"
exit7 = re.compile(r'\brennt\b.{,20}(\bdavon\b|\bhinaus\b)|(\bdavon\b|\bhinaus\b).{,20}\brennt\b')
exit8 = re.compile(r'^\ballein\b(\.)?$')
exit9 = re.compile(r'\bflieh(t|en)\b')
exit10 = re.compile(r'^.{,20}\bgeh(t|en|n)\b(\.)?$')
exit11 = re.compile(r'\bnacheilend\b')
exit12 = re.compile(r'\beil(t|en)\b.{,20}\bab\b')


#regular expressions for words that may not appear with other regex
wrongWord = re.compile(r'\bwill\b')
wrongWord2 = re.compile(r'\blaut\b|\bleise\b|\bzu(m|r)?\b(?!\spferd)|\bgegen\b|\bentgegen\b|\bweisend\b') # e.g. "zu XY" (talking) -> no entrance, but "zu Pferde" marks an entrance


def readPersonList(personElements: list) -> dict:
    """reads the personList and extracts the names with the corresponding ID in a dictionary

    Args:
        personElements (list): all person- and personGrp-elements from the persList

    Returns:
        dict: dictionary with person names as keys and the corresponding IDs as values 
    """
    persNameID = {}
    figurenNamen = []

    for person in personElements:
        id = person.attrib['{http://www.w3.org/XML/1998/namespace}id']
        names = person.xpath('.//tei:persName | .//tei:name', namespaces=namespace) #get all names of persons (even variants)
        for name in names:
            name = name.text.lower()
            name = name.translate(str.maketrans("", "", string.punctuation))

            nameTokens = nlp(name)
            if len(nameTokens)>1 and (nameTokens[0].pos_ == "DET" or nameTokens[0].pos_ == "PRON"):   #check if first word in the persons name is an article (der, die, das, ein, einer, eine, o.Ä.) (should be removed)
                name = name.replace(nameTokens[0].text, '').strip()
 
            figurenNamen.append(name)
            persNameID[name] = id
    return persNameID


def findPersons(stageText: str, namesWithIDs: dict) -> str:
    """extracts the corresponding person(s) to a detected entrance or exit and add their IDs in a string

    Args:
        stageText (str): the text of a stage tag
        namesWithIDs (dict): the names of all persons with the corresponding IDs

    Returns:
        str: returns all the IDs of the persons in a string in the following scheme "#person1 #person2 ..."
    """
    detectedPersons = set()
    persons = ""
    for word in stageText.split():
        word = word.translate(str.maketrans('', '', string.punctuation))  #remove punctuations from words
        if word in namesWithIDs:
            detectedPersons.add(namesWithIDs[word])
    for name in namesWithIDs:
        if name in stageText:
            detectedPersons.add(namesWithIDs[name])
    
    for idx2, person in enumerate(detectedPersons):
        if idx2>0:
            persons += " #"+person
        else:
            persons += "#"+person
    
    return persons

def removePersons(presentPersons: str, gonePersons: str) -> str:
    """update the presentPersons if persons have left

    Args:
        presentPersons (str): persons that are present on the stage
        gonePersons (str): persons who left the stage

    Returns:
        str: updated string for the persons that are on stage
    """

    persons = presentPersons.split()
    gonePersons = gonePersons.split()

    personSet = set()

    persons = ""

    for person in persons:
        if person not in gonePersons:
            personSet.add(person)

    for idx2, person in enumerate(personSet):
        if idx2>0:
            persons += " "+person
        else:
            persons += person
    
    return persons


def addPersons(presentPersons: str, arrivedPersons: str) -> str:
    """update the present persons if new persons entered the stage

    Args:
        presentPersons (str): persons that are present on stage
        arrivedPersons (str): persons that entered the stage

    Returns:
        str: updated string for the persons that are on stage
    """
    persons = presentPersons.split()
    arrPersons = arrivedPersons.split()

    personSet = set()

    persons = ""

    for person in persons:
        personSet.add(person)
    
    for arrPerson in arrivedPersons:
        if arrPerson not in persons:
            personSet.add(arrPerson)

    for idx2, person in enumerate(personSet):
        if idx2>0:
            persons += " "+person
        else:
            persons += person
    
    return persons


#for drama in dramas:
    
for file in os.listdir(directory):
    filename = os.fsdecode(file)

    print("in progress: " +filename)
    namespace = {'tei':'http://www.tei-c.org/ns/1.0'}
    #try to get the files with the xml encoded dramatic text
    try:
        #rel_path = "unannotated-texts/"+drama +".xml"
        abs_file_path = os.path.join(directory, file)
        #abs_file_path = os.path.normpath(abs_file_path)
        tree = ET.parse(abs_file_path)
    except Exception as e:
        print("Failed to load file. Please check file path. File will be skipped.")
        continue
    root = tree.getroot() 

    #extract person and personGrp-elements from the person list (persList-element)
    persons = root.xpath(".//tei:person | .//tei:personGrp" , namespaces = namespace)
    
    #get dictionary with person names and IDs
    namesWithIDs = readPersonList(persons)

    previousPersons =""

    divs = root.xpath(".//tei:div[@type='scene']", namespaces=namespace)
    
    if len(divs) == 0:
        divs = root.xpath(".//tei:div[@type='act']", namespaces=namespace)
    

    for div in divs:
        stage = div.findall(".//tei:stage", namespaces = namespace)

        #remember persons that are on the stage
        presentPersons = ""

        for idx, s in enumerate(stage):
            persons =""

            #if the stage-element contains a pb-element, that marks the beginning of a new page, the text cannot be accessed via s.text
            #in this case, the text can be accessed via s.tail
            if(not s.text):
                stageText = "".join((s.tail).split())
            else:
                stageText = " ".join((s.text).split())

            #lowercase stage-text
            stageText = stageText.lower()
            #split the text in individual sentences by . or ;
            sentences = re.split("\.|;", stageText)
            #remove the sentences that are None
            sentences = list(filter(None, sentences))


            #### check for entrances ####
            if(s.getprevious() is not None):
                previoustext  = s.getprevious()
                #get the text of the previous element
                #to avoid errors, because there can be a pb-elemen in between an element, some checks are necessary to access the text the right way without raising an error
                if(not s.getprevious().text):
                    if(s.getprevious().tail and s.getprevious().tail.strip()):
                        previoustext = s.getprevious().tail
                    else:
                        if len(s.getprevious().getchildren())>0:
                            previoustext = s.getprevious().getchildren()[0].tail
                        else:
                            previoustext = ""
                else:
                    previoustext = previoustext.text

                if(s.getprevious().tag == "{http://www.tei-c.org/ns/1.0}head" and "Auftritt" in previoustext):
                    s.set("type", "entrance")
                    persons = findPersons(stageText, namesWithIDs)

                    #get the corresponding persons that are mentioned with "die Vorigen"
                    if("vorige" in stageText and previousPersons != ""):
                        persons += " " + previousPersons

                        #remove duplicates
                        words = persons.split()
                        persons = " ".join(sorted(set(words), key=words.index))  
                    s.set("who", persons)
                    previousPersons = persons
                    presentPersons = persons
                    continue
            for sentence in sentences:
                text = sentence.lower() #ignore case
                if(entrances1.search(text) or entrances2.search(text) or entrances3.search(text) or entrances4.search(text) or entrances5.search(text) or entrances6.search(text) or entrances7.search(text)):
                    if(wrongWord.search(text)): #skip sentence, if word like "will" appears in the sentence
                        continue
                    s.set("type", "entrance")
                    persons = findPersons(text, namesWithIDs)
                    for element in s.iterancestors('{http://www.tei-c.org/ns/1.0}sp'):  #looking for a parent sp-Tag to get person that is currently speaking
                        if persons == "":
                            persons = element.attrib['who']

                    if 'who' in s.attrib:
                        persons +=" "+ s.attrib['who']
                        words = persons.split()
                        persons = " ".join(sorted(set(words), key=words.index))  #remove duplicates
                    presentPersons = addPersons(presentPersons, persons)
                    s.set("who", persons)

                #### check for exits ####
                elif(exit1.search(text) or exit2.search(text) or exit3.search(text) or exit4.search(text) or exit5.search(text) or exit6.search(text) or exit7.search(text)  or exit9.search(text) or exit10.search(text) or exit11.search(text) or exit12.search(text)): #or exit2.search(text) #"or exit8.search(text)"
                    if(wrongWord.search(text)): #skip sentence, if word like "will" appears in the sentence
                        continue
                    s.set("type", "exit")
                    persons = findPersons(text, namesWithIDs)

                    for element in s.iterancestors('{http://www.tei-c.org/ns/1.0}sp'):  #looking for a parent sp-Tag to get person that is currently speaking
                        if persons == "":
                            persons = element.attrib['who']

                    if 'who' in s.attrib:
                        persons +=" "+ s.attrib['who']
                        words = persons.split()
                        persons = " ".join(sorted(set(words), key=words.index))  #remove duplicates
                    s.set("who", persons)

                    previousPersons = removePersons(previousPersons, persons)
                    presentPersons = removePersons(presentPersons, persons)
                
                #### special case: regex with word "allein" can indicate an exit or entrance ####
                elif(exit8.search(text)):
                    persons = findPersons(text, namesWithIDs)
                    for element in s.iterancestors('{http://www.tei-c.org/ns/1.0}sp'):  #looking for a parent sp-Tag to get person that is currently speaking
                        if persons == "":
                            persons = element.attrib['who']
                    if persons in presentPersons:
                        s.set("type", "exit")
                        gonePersons = removePersons(presentPersons, persons)
                        s.set("who", gonePersons)
                    else:
                        s.set("type", "entrance")
                        s.set("who", persons)
                        presentPersons = removePersons(presentPersons, persons)


                #### check if sentence contains no verbs but person names ####
                else: 
                    doc = nlp(text) #part-of-speech tagging
                    noVerb = False
                    for token in doc: #check if sentence contains at least one verb
                        if token.pos_ == 'VERB':
                            noVerb = True
                            break
                    if noVerb == False: 
                        persons = findPersons(text, namesWithIDs)
                        if not(persons == ''): # only an entrance, if sentence contains at least one person name
                            if(wrongWord2.search(text)): # skip sentence, if it contains words like "leise" or "laut" 
                                continue
                            s.set("type", "entrance")
                            if 'who' in s.attrib:
                                persons +=" "+ s.attrib['who']
                                words = persons.split()
                                persons = " ".join(sorted(set(words), key=words.index))  #remove duplicates
                            s.set("who", persons)
                            presentPersons = addPersons(presentPersons, persons)
                            continue

    et = ET.ElementTree(root)
    rel_path = "automatically-annotated-texts/"+filename
    abs_file_path = os.path.join(script_dir, rel_path)
    abs_file_path = os.path.normpath(abs_file_path)
    et.write(abs_file_path, pretty_print=True, xml_declaration=True,   encoding="utf-8") #save new xml file with extended stage-elements
    print("successfully completed: "+ filename)