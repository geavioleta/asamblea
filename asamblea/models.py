from django.db import models
import json, random

class Member(models.Model):
	public_key = models.CharField(max_length=100)
	signup_code = models.CharField(max_length=50)
	unredeemed_invites = models.TextField()
	unsent_invites = models.TextField()
	intersect_requests = models.TextField(default='')
	outer_profile_DK = models.CharField(max_length=250, default='')
	outer_profile_EK = models.CharField(max_length=100, default='')
	inner_profile_DK = models.CharField(max_length=250, default='')
	inner_profile_EK = models.CharField(max_length=100, default='')
	intersections = models.IntegerField(default=0)

	def get_invite(self):
		unsent_invites = json.loads(self.unsent_invites)
		unredeemed_invites = json.loads(self.unredeemed_invites)
		if len(unsent_invites) == 0:
			string = "no invites remaining"
			if len(unredeemed_invites) > 0:
				string += " (but you have unredeemed invites)"
			return string
		invite = unsent_invites.pop()
		unredeemed_invites.append(invite)
		self.unsent_invites = json.dumps(unsent_invites)
		self.unredeemed_invites = json.dumps(unredeemed_invites)
		return invite

	def redeem_invite(self, code):
		unredeemed_invites = json.loads(self.unredeemed_invites)
		for invite in unredeemed_invites:
			if invite==code:
				unredeemed_invites.remove(invite)
				return True
		return False

	def request_intersect(self, pubkey):
		intersect_requests = json.loads(self.intersect_requests)
		intersect_requests.append(pubkey)
		self.intersect_requests = json.dumps(intersect_requests)

	def clear_request(self, pubkey):
		intersect_requests = json.loads(self.intersect_requests)
		intersect_requests.remove(pubkey)
		self.intersect_requests = json.dumps(intersect_requests)

	def __str__(self):
		return self.public_key
