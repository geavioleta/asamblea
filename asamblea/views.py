from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import base64, hashlib, os, random, time, json
import boto3
from ecies import encrypt
from asamblea.models import Member

def index(request):
	return render(request, "index.html")

def init_signup(request):
	outer_profile_dk = request.POST.get("outerProfileDK", None)
	outer_profile_ek = request.POST.get('outerProfileEK', None)
	inner_profile_dk = request.POST.get("innerProfileDK", None)
	inner_profile_ek = request.POST.get('innerProfileEK', None)
	public_key = request.POST.get("pubkey", None)
	admin = request.POST.get("admin", "no")
	code = request.POST.get("code", None)
	member_pk = request.POST.get("invitedBy", None)
	try:
		m = Member.objects.get(public_key=public_key)
		raise ValueError('New member public key already exists')
	except:
		pass
	if admin=="yes" and len(Member.objects.all()) < 100:
		unsent_invites = json.dumps([randomString(20) for _ in range(100)])
		unredeemed_invites = json.dumps([])
		intersect_requests = json.dumps([])
		m=Member(public_key=public_key, outer_profile_DK=outer_profile_dk, outer_profile_EK=outer_profile_ek, inner_profile_DK=inner_profile_dk, inner_profile_EK=inner_profile_ek, signup_code=code, unsent_invites=unsent_invites, unredeemed_invites=unredeemed_invites, intersect_requests=intersect_requests)
		m.save()
	else:
		invited_by = Member.objects.get(public_key=member_pk)
		if invited_by.redeem_invite(code):
			unsent_invites = json.dumps([randomString(20) for _ in range(10)])
			unredeemed_invites = json.dumps([])
			intersect_requests = json.dumps([])
			m=Member(public_key=public_key, outer_profile_DK=outer_profile_dk, outer_profile_EK=outer_profile_ek, inner_profile_DK=inner_profile_dk, inner_profile_EK=inner_profile_ek, signup_code=code, unsent_invites=unsent_invites, unredeemed_invites=unredeemed_invites, intersect_requests=intersect_requests)
			m.save()
		else:
			raise ValueError('Invitation invalid or already redeemed')
	outer = encrypt(m.outer_profile_EK, json.dumps({'alias':'', 'publicKey': public_key, 'tags': '', 'intro':'', 'intersections': '0', 'imgData':''}).encode())
	inner = encrypt(m.inner_profile_EK, json.dumps({'name':'', 'email':'', 'location':'', 'about': '', 'announcements':'', 'intersections':{}, 'posts':{}}).encode())
	member_storage(m, outer, "outerProfile.enc")
	member_storage(m, inner, "innerProfile.enc")
	return JsonResponse({'status': "ok"})

def init_login(request):
	public_key = request.POST.get("pubkey", None)
	m = Member.objects.get(public_key=public_key)
	m.save()
	return JsonResponse({'code': m.signup_code, 'innerProfileDK':m.inner_profile_DK, 'outerProfileDK':m.outer_profile_DK})

def store_profile(request):
	public_key = request.POST.get("pubkey", None)
	profile = request.POST.get("profile", None)
	profile_type = request.POST.get("profileType", None)
	if profile_type == "outer":
		fname = "outerProfile.enc"
	elif profile_type == "inner":
		fname = "innerProfile.enc"
	else:
		raise ValueError('Improper profileType')
	m = Member.objects.get(public_key=public_key)
	member_storage(m, base64.b64decode(profile), fname)
	return JsonResponse({'status': 'ok'})

def store_intersection(request):
	public_key = request.POST.get("pubkey", None)
	contact_pk = request.POST.get("contactPK", None)
	profile_key = request.POST.get("profileKey", None)
	profile_type = request.POST.get("profileType", None)
	is_request = request.POST.get("isRequest", None)
	if profile_type == "outer":
		fname = contact_pk+"/outerKey.enc"
	elif profile_type == "inner":
		fname = contact_pk+"/innerKey.enc"
	else:
		raise ValueError('Improper profileType')
	m = Member.objects.get(public_key=public_key)
	if is_request == "yes":
		receiver = Member.objects.get(public_key=contact_pk)
		receiver.request_intersect(public_key)
		receiver.save()
	print("got this far!")
	member_storage(m, base64.b64decode(profile_key), fname)
	return JsonResponse({'status': 'ok'})

def next_invite(request):
	public_key = request.POST.get("pubkey", None)
	m = Member.objects.get(public_key=public_key)
	invite = m.get_invite()
	m.save()
	return JsonResponse({'invite':invite})

def get_full_profile(request):
	public_key = request.POST.get("pubkey", None)
	east = boto3.Session(region_name = 'us-east-1')
	s3 = east.resource('s3', aws_access_key_id=os.environ.get('AWS_ACCESS_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))
	temp_name = randomString(20)
	inner_file = public_key+"/innerProfile.enc"
	s3.meta.client.download_file('asamblea-social', inner_file, os.path.join(os.path.dirname(__file__), temp_name))
	with open(os.path.join(os.path.dirname(__file__), temp_name), "rb") as f:
		inner_data = f.read()
	os.remove(os.path.join(os.path.dirname(__file__), temp_name))
	outer_file = public_key+"/outerProfile.enc"
	s3.meta.client.download_file('asamblea-social', outer_file, os.path.join(os.path.dirname(__file__), temp_name))	
	with open(os.path.join(os.path.dirname(__file__), temp_name), "rb") as f:
		outer_data = f.read()
	os.remove(os.path.join(os.path.dirname(__file__), temp_name))
	return JsonResponse({"innerProfile": base64.b64encode(inner_data).decode('utf-8'), 'outerProfile': base64.b64encode(outer_data).decode('utf-8')})

def get_intersect_requests(request):
	public_key = request.POST.get("pubkey", None)
	east = boto3.Session(region_name = 'us-east-1')
	s3 = east.resource('s3', aws_access_key_id=os.environ.get('AWS_ACCESS_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))
	m = Member.objects.get(public_key=public_key)
	new_reqs = json.loads(m.intersect_requests)
	new_outer = []
	outer_pubs = []
	new_inner = []
	inner_pubs = []
	temp_name = randomString(20)
	for r in new_reqs:
		try:
			rfile = r+"/"+public_key+"/innerKey.enc"
			s3.meta.client.download_file('asamblea-social', rfile, os.path.join(os.path.dirname(__file__), temp_name))
			with open(os.path.join(os.path.dirname(__file__), temp_name), "rb") as f:
				data = f.read()
			os.remove(os.path.join(os.path.dirname(__file__), temp_name))
			inner = base64.b64encode(data).decode('utf-8')
			rfile = r+"/"+public_key+"/outerKey.enc"
			s3.meta.client.download_file('asamblea-social', rfile, os.path.join(os.path.dirname(__file__), temp_name))
			with open(os.path.join(os.path.dirname(__file__), temp_name), "rb") as f:
				data = f.read()
			os.remove(os.path.join(os.path.dirname(__file__), temp_name))
			new_outer.append(base64.b64encode(data).decode('utf-8'))
			outer_pubs.append(r)
			new_inner.append(inner)
			inner_pubs.append(r)
		except:
			try:
				rfile = r+"/"+public_key+"/outerKey.enc"
				s3.meta.client.download_file('asamblea-social', rfile, os.path.join(os.path.dirname(__file__), temp_name))
				with open(os.path.join(os.path.dirname(__file__), temp_name), "rb") as f:
					data = f.read()
				os.remove(os.path.join(os.path.dirname(__file__), temp_name))
				new_outer.append(base64.b64encode(data).decode('utf-8'))
				outer_pubs.append(r)
			except:
				pass
	return JsonResponse({'outerPubs': outer_pubs, 'outerProfs': new_outer, 'innerPubs': inner_pubs, 'innerProfs': new_inner})

def get_intersection(request):
	public_key = request.POST.get("pubkey", None)
	get_key = request.POST.get("getkey", None)
	east = boto3.Session(region_name = 'us-east-1')
	s3 = east.resource('s3', aws_access_key_id=os.environ.get('AWS_ACCESS_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))
	m = Member.objects.get(public_key=public_key)
	temp_name = randomString(20)
	innerFile = ""
	outerFile = ""
	try:
		rfile = get_key+"/"+public_key+"/innerKey.enc"
		s3.meta.client.download_file('asamblea-social', rfile, os.path.join(os.path.dirname(__file__), temp_name))
		with open(os.path.join(os.path.dirname(__file__), temp_name), "rb") as f:
			data = f.read()
		os.remove(os.path.join(os.path.dirname(__file__), temp_name))
		innerFile = base64.b64encode(data).decode('utf-8')
		rfile = get_key+"/"+public_key+"/outerKey.enc"
		s3.meta.client.download_file('asamblea-social', rfile, os.path.join(os.path.dirname(__file__), temp_name))
		with open(os.path.join(os.path.dirname(__file__), temp_name), "rb") as f:
			data = f.read()
		os.remove(os.path.join(os.path.dirname(__file__), temp_name))
		outerFile = base64.b64encode(data).decode('utf-8')
	except:
		try:
			rfile = get_key+"/"+public_key+"/outerKey.enc"
			s3.meta.client.download_file('asamblea-social', rfile, os.path.join(os.path.dirname(__file__), temp_name))
			with open(os.path.join(os.path.dirname(__file__), temp_name), "rb") as f:
				data = f.read()
			os.remove(os.path.join(os.path.dirname(__file__), temp_name))
			outerFile = base64.b64encode(data).decode('utf-8')
		except:
			raise ValueError("No intersection exists")
	return JsonResponse({'outerProfileKey': outerFile, 'innerProfileKey': innerFile})

def clear_intersect_request(request):
	public_key = request.POST.get("pubkey", None)
	to_clear = request.POST.get("toClear", None)
	m = Member.objects.get(public_key=public_key)
	print(m.intersect_requests)
	print(to_clear)
	m.clear_request(to_clear)
	m.save()
	return JsonResponse({'status': 'ok'})

def get_unredeemed(request):
	public_key = request.POST.get("pubkey", None)
	m = Member.objects.get(public_key=public_key)
	return JsonResponse({'unredeemed': m.unredeemed_invites})

def member_storage(member, data, fname):
	pk = member.public_key
	east = boto3.Session(region_name = 'us-east-1')
	s3 = east.resource('s3', aws_access_key_id=os.environ.get('AWS_ACCESS_ID'), aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'))
	filename = randomString(20)
	with open(os.path.join(os.path.dirname(__file__), filename), "wb") as f:
		f.write(data)
	s3.meta.client.upload_file(os.path.join(os.path.dirname(__file__), filename), 'asamblea-social', pk+"/"+fname)
	os.remove(os.path.join(os.path.dirname(__file__), filename))

def randomString(n):
	chars = "a b c d e f g h i j k l m n o p q r s t u v q x y z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z 1 2 3 4 5 6 7 8 9".split()
	return "".join([random.choice(chars) for _ in range(n)])
