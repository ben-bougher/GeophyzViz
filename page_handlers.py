"""
Handler classes for serving html webpages
"""
from google.appengine.ext import webapp as webapp2

class MainHandler(webapp2):

    def get(self):

        
# For image serving
import cloudstorage as gcs

from PIL import Image

import urllib
import urllib2
import time

import hashlib
import logging

import stripe

import json
import base64

from xml.etree import ElementTree

from constants import admin_id, env, PRICE, UR_STATUS_DICT, \
    tax_dict, stripe_public_key, usgs_colours

from lib_auth import AuthExcept, get_cookie_string, signup, signin, \
    verify, authenticate, verify_signup, initialize_user,\
    reset_password, \
    forgot_password, send_message, make_user, cancel_subscription

from lib_db import Rock, Scenario, User, ModelrParent, Group, \
    GroupRequest, ActivityLog, ModelServedCount,\
    ImageModel, Issue, EarthModel, Server, Fluid,\
    get_all_items_user

from lib_util import RGBToString


class ModelrPageRequest(webapp2.RequestHandler):
    """
    Base class for modelr app pages. Allows commonly used functions
    to be inherited to other pages.
    """

    def get_base_params(self, **kwargs):
        '''
        get the default parameters used in base_template.html
        '''

        user = self.verify()

        if user:
            email_hash = hashlib.md5(user.email).hexdigest()
        else:
            email_hash = ''

        hostname = Server.all()\
                         .ancestor(ModelrParent.all().get()).get().host
        
        default_rock = dict(vp=0, vs=0, rho=0, vp_std=0,
                            rho_std=0, vs_std=0,
                            description='description',
                            name='name', group='public')

        params = dict(logout=users.create_logout_url(self.request.uri),
                      HOSTNAME=hostname,
                      current_rock=default_rock,
                      email_hash=email_hash)

        params.update(kwargs)
        return params

    def verify(self):
        """
        Verify that the current user is a legimate user. Returns the
        user object from the database if true, otherwise returns None.
        """

        cookie = self.request.cookies.get('user')
        if cookie is None:
            return

        try:
            user, password = cookie.split('|')
        except ValueError:
            return

        return verify(user, password, ModelrParent.all().get())


class MainHandler(ModelrPageRequest):
    '''
    main page
    '''
    def get(self):

        # Redirect to the dashboard if the user is logged in
        user = self.verify()
        if user:
            self.redirect('/dashboard')

        template_params = self.get_base_params()
        template = env.get_template('index.html')
        html = template.render(template_params)

        self.response.out.write(html)


class ScenarioPageHandler(ModelrPageRequest):
    '''
      Display the scenario page (uses scenario.html template)
    '''
    def get(self):

        # Check for a user, but allow guests as well
        user = self.verify()

        self.response.headers['Content-Type'] = 'text/html'
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        hdrs = 'X-Request, X-Requested-With'
        self.response.headers['Access-Control-Allow-Headers'] = hdrs

        # Get the default rocks
        default_rocks = Rock.all().order('name')
        default_rocks.filter("user =", admin_id)
        default_rocks = default_rocks.fetch(100)

        # Get the user rocks
        if user:
            rocks = Rock.all().order('name').ancestor(user).fetch(100)

            # Get the group rocks
            group_rocks = []
            for group in user.group:
                g_rocks = Rock.all()\
                              .order('name')\
                              .ancestor(ModelrParent.all().get())\
                              .filter("group =", group)
                group_rocks.append({"name": group.capitalize(),
                                    "rocks": g_rocks.fetch(100)})

            # Get the users scenarios
            scenarios = \
                Scenario.all().ancestor(user)\
                              .filter("user =", user.user_id).fetch(100)
        else:
            rocks = []
            group_rocks = []
            scenarios = []

        # Get Evan's default scenarios (user id from modelr database)
        scen = Scenario.all().ancestor(ModelrParent.all().get())
        scen = scen.filter("user =", admin_id).fetch(100)
        if scen:
            scenarios += scen

        model_data = EarthModel.all()\
                               .filter("user =", admin_id).fetch(1000)

        # Get the models from uploaded images
        if user:
            user_data = EarthModel.all()\
                                  .filter("user =", user.user_id)\
                                  .fetch(1000)

            model_data = model_data + user_data

        earth_models = [{"image_key": str(i.parent_key()),
                         "name": i.name} for i in model_data]

        template_params = self.get_base_params(user=user, rocks=rocks,
                                               default_rocks=default_rocks,
                                               group_rocks=group_rocks,
                                               scenarios=scenarios,
                                               earth_models=earth_models)

        template = env.get_template('scenario.html')

        html = template.render(template_params)

        if user:
            activity = "viewed_scenario"
            ActivityLog(user_id=user.user_id,
                        activity=activity,
                        parent=ModelrParent.all().get()).put()
        self.response.out.write(html)


class DashboardHandler(ModelrPageRequest):
    '''
    Display the dashboard page (uses dashboard.html template)
    '''
    @authenticate
    def get(self, user):

        template_params = self.get_base_params(user=user)

        self.response.headers['Content-Type'] = 'text/html'

        # Get all the rocks
        rocks = Rock.all()
        rocks.ancestor(user)
        rocks.filter("user =", user.user_id)
        rocks.order("-date")

        default_rocks = Rock.all()
        default_rocks.filter("user =", admin_id)

        rock_groups = []
        for name in user.group:
            dic = {'name': name.capitalize(),
                   'rocks': Rock.all().ancestor(ModelrParent.all().get())
                   .filter("group =", name).fetch(100)}
            rock_groups.append(dic)

        # Get all the fluids
        fluids = Fluid.all()
        fluids.ancestor(user)
        fluids.filter("user =", user.user_id)
        fluids.order("-date")

        default_fluids = Fluid.all()
        default_fluids.filter("user =", admin_id)

        fluid_groups = []
        for name in user.group:
            dic = {'name': name.capitalize(),
                   'fluids': Fluid.all().ancestor(ModelrParent.all().get())
                   .filter("group =", name).fetch(100)}
            fluid_groups.append(dic)

        # Get all the user scenarios
        scenarios = Scenario.all()
        if not user.user_id == admin_id:
            scenarios.ancestor(user)
        else:
            scenarios.ancestor(ModelrParent.all().get())

        scenarios.filter("user =", user.user_id)
        scenarios.order("-date")

        for s in scenarios.fetch(100):
            logging.info((s.name, s))

        if user.user_id != admin_id:
            default_image_models = ImageModel.all()\
                                             .filter("user =", admin_id)\
                                             .fetch(100)
        else:
            default_image_models = []
        
        user_image_models = ImageModel.all()\
                                      .filter("user =", user.user_id)\
                                      .fetch(100)
        
        default_models = [{"image": images.get_serving_url(i.image,
                                                           size=200,
                                                           crop=False,
                                                           secure_url=True),
                           "image_key": str(i.key()),
                           "editable": False,
                           "models": EarthModel.all().ancestor(i)
                           .filter("user =", user.user_id).fetch(100)}
                          for i in default_image_models]

        user_models = [{"image": images.get_serving_url(i.image,
                                                        size=200,
                                                        crop=False,
                                                        secure_url=True),
                        "image_key": str(i.key()),
                        "editable": True,
                        "models": EarthModel.all().ancestor(i)
                        .filter("user =", user.user_id).fetch(100)}
                       for i in user_image_models]

        models = user_models + default_models

        template_params.update(rocks=rocks.fetch(100),
                               scenarios=scenarios.fetch(100),
                               default_rocks=default_rocks.fetch(100),
                               rock_groups=rock_groups,
                               fluids=fluids.fetch(100),
                               default_fluids=default_fluids.fetch(100),
                               fluid_groups=fluid_groups,
                               models=models)

        # Check if a rock is being edited
        if self.request.get("selected_rock"):
            rock_id = self.request.get("selected_rock")
            current_rock = Rock.get_by_id(int(rock_id),
                                          parent=user)
            template_params['current_rock'] = current_rock
        else:
            current_rock = Rock()
            current_rock.name = "name"
            current_rock.description = "description"
            current_rock.vp = 3000.0
            current_rock.vs = 1500.0
            current_rock.rho = 2500.0
            current_rock.vp_std = 50.0
            current_rock.vs_std = 50.0
            current_rock.rho_std = 50.0

            template_params['current_rock'] = current_rock

        # Check if a fluid is being edited
        if self.request.get("selected_fluid"):
            fluid_id = self.request.get("selected_fluid")
            current_fluid = Fluid.get_by_id(int(fluid_id),
                                            parent=user)
            template_params['current_fluid'] = current_fluid
        else:
            current_fluid = Fluid()
            current_fluid.name = "name"
            current_fluid.description = "description"
            current_fluid.vp = 1500.0
            current_fluid.K = 200.0

        template_params['current_fluid'] = current_fluid
        template = env.get_template('dashboard.html')
        html = template.render(template_params)

        activity = "dashboard"
        ActivityLog(user_id=user.user_id,
                    activity=activity,
                    parent=ModelrParent.all().get()).put()
        self.response.out.write(html)

# class AboutHandler(ModelrPageRequest):
#     def get(self):

#         # Uptime robot API key for modelr.io
#         #ur_api_key_modelr_io = 'm775980219-706fc15f12e5b88e4e886992'
#         # Uptime Robot API key for modelr.org REL
#         #ur_api_key_modelr_org = 'm775980224-e2303a724f89ef0ab886558a'
#         # Uptime Robot API key for modelr.org DEV
#         #ur_api_key_modelr_org = 'm776083114-e34c154f2239e7c273a04dd4'

#         ur_api_key = 'u108622-bd0a3d1e36a1bf3698514173'

#         # Uptime Robot IDs
#         ur_modelr_io = '775980219'
#         ur_modelr_org = '775980224'  # REL, usually

#         # Uptime Robot URL
#         ur_url = 'http://api.uptimerobot.com/getMonitors'

#         params = {'apiKey': ur_api_key,
#           'monitors': ur_modelr_io + '-' + ur_modelr_org,
#           'customuptimeratio': '30',
#           'format': 'json',
#           'nojsoncallback':'1',
#           'responseTimes':'1'
#          }

#         # A dict is easily converted to an HTTP-safe query string.
#         ur_query = urllib.urlencode(params)

#         # Opened URLs are file-like.
#         full_url = '{0}?{1}'.format(ur_url, ur_query)
#         try:
#             f = urllib2.urlopen(full_url)
#             raw_json = f.read()

#         except Exception as e:
#             print "Failed to retrieve stats.",
#             print "Uptime Robot may be down:", e

#         user = self.verify()
#         models_served = ModelServedCount.all().get()

#         try:
#             j = json.loads(raw_json)
            
#             ur_ratio = j['monitors']['monitor'][0]['customuptimeratio']
#             ur_server_ratio = j['monitors']['monitor'][1]['customuptimeratio']
#             ur_server_status_code = j['monitors']['monitor'][1]['status']
#             ur_last_response_time = j['monitors']['monitor'][0]['responsetime'][-1]['value']
#             ur_last_server_response_time = j['monitors']['monitor'][1]['responsetime'][-1]['value']
            
#             ur_server_status = UR_STATUS_DICT[ur_server_status_code].upper()
            
#             template_params = \
#             self.get_base_params(user=user,
#                                  ur_ratio=ur_ratio,
#                                  ur_response_time=ur_last_response_time,
#                                  ur_server_ratio=ur_server_ratio,
#                                  ur_server_status=ur_server_status,
#                                  ur_server_response_time=ur_last_server_response_time,
#                                  models_served=models_served.count
#                                  )
#         except:

#             template_params = \
#             self.get_base_params(user=user,
#                                  ur_ratio=None,
#                                  ur_response_time=None,
#                                  ur_server_ratio=None,
#                                  ur_server_status="Unknown",
#                                  ur_server_response_time=None,
#                                  models_served=models_served.count
#                                  )

        
#         template = env.get_template('about.html')
#         html = template.render(template_params)
#         self.response.out.write(html)          
     
class AboutHandler(ModelrPageRequest):
    def get(self):

        # Uptime robot API key for modelr.io
        #ur_api_key_modelr_io = 'm775980219-706fc15f12e5b88e4e886992'
        # Uptime Robot API key for modelr.org REL
        #ur_api_key_modelr_org = 'm775980224-e2303a724f89ef0ab886558a'
        # Uptime Robot API key for modelr.org DEV
        #ur_api_key_modelr_org = 'm776083114-e34c154f2239e7c273a04dd4'

        ur_api_key = 'u108622-bd0a3d1e36a1bf3698514173'

        # Uptime Robot IDs
        ur_modelr_io = '775980219'
        ur_modelr_org = '775980224'  # REL, usually

        # Uptime Robot URL
        ur_url = 'http://api.uptimerobot.com/getMonitors'

        params = {'apiKey': ur_api_key,
          'monitors': ur_modelr_io + '-' + ur_modelr_org,
          'customuptimeratio': '30',
          'format': 'json',
          'nojsoncallback':'1',
          'responseTimes':'1'
         }

        # A dict is easily converted to an HTTP-safe query string.
        ur_query = urllib.urlencode(params)

        # Opened URLs are file-like.
        full_url = '{0}?{1}'.format(ur_url, ur_query)
        try:
            f = urllib2.urlopen(full_url)
            raw_json = f.read()

        except Exception as e:
            print "Failed to retrieve stats.",
            print "Uptime Robot may be down:", e

        user = self.verify()
        models_served = ModelServedCount.all().get()

        try:
            j = json.loads(raw_json)
            
            ur_ratio = j['monitors']['monitor'][0]['customuptimeratio']
            ur_server_ratio = j['monitors']['monitor'][1]['customuptimeratio']
            ur_server_status_code = j['monitors']['monitor'][1]['status']
            ur_last_response_time = j['monitors']['monitor'][0]['responsetime'][-1]['value']
            ur_last_server_response_time = j['monitors']['monitor'][1]['responsetime'][-1]['value']
            
            ur_server_status = UR_STATUS_DICT[ur_server_status_code].upper()
            
            template_params = \
            self.get_base_params(user=user,
                                 ur_ratio=ur_ratio,
                                 ur_response_time=ur_last_response_time,
                                 ur_server_ratio=ur_server_ratio,
                                 ur_server_status=ur_server_status,
                                 ur_server_response_time=ur_last_server_response_time,
                                 models_served=models_served.count
                                 )
        except:

            template_params = \
            self.get_base_params(user=user,
                                 ur_ratio=None,
                                 ur_response_time=None,
                                 ur_server_ratio=None,
                                 ur_server_status="Unknown",
                                 ur_server_response_time=None,
                                 models_served=models_served.count
                                 )

        
        template = env.get_template('about.html')
        html = template.render(template_params)
        self.response.out.write(html)          


class FeaturesHandler(ModelrPageRequest):
    def get(self):

        user = self.verify()
        template_params = self.get_base_params(user=user)
        template = env.get_template('features.html')
        html = template.render(template_params)
        self.response.out.write(html)      


class FeedbackHandler(ModelrPageRequest):

    @authenticate
    def get(self, user):

        template_params = self.get_base_params(user=user)

        # Get the list of issues from GitHub.
        # First, set up the request.
        gh_api_key = 'token 89c9d30cddd95358b1465d1dacb1b64597b42f89'
        url = 'https://api.github.com/repos/kwinkunks/modelr_app/issues'
        params = {'labels': 'wishlist', 'state': 'open'}
        query = urllib.urlencode(params)
        full_url = '{0}?{1}'.format(url, query)

        # Now make the request.
        req = urllib2.Request(full_url)
        req.add_header('Authorization', gh_api_key)

        try:
            resp = urllib2.urlopen(req)
            raw_json = resp.read()
            git_data = json.loads(raw_json)

        except:
            err_msg = ('Failed to retrieve issues from GitHub. ' +
                       'Please check back later.')
            git_data = {}

        else:
            err_msg = ''

            for issue in git_data:

                # Get the user's opinion.
                status = None
                if user:
                    user_issues = Issue.all().ancestor(user)
                    user_issue = user_issues.filter("issue_id =",
                                                    issue["id"]).get()
                    if user_issue:
                        status = user_issue.vote
                    else:
                        Issue(parent=user, issue_id=issue["id"]).put()

                up, down = 0, 0

                if status == 1:
                    up = 'true'
                if status == -1:
                    down = 'true'

                issue.update(status=status,
                             up=up,
                             down=down)

                # Get the count. We have to read the database twice.
                down_votes = Issue.all().ancestor(ModelrParent.all().get())\
                                        .filter("issue_id =", issue["id"])\
                                        .filter("vote =", -1).count()
                up_votes = Issue.all().ancestor(ModelrParent.all().get())\
                                      .filter("issue_id =", issue["id"])\
                                      .filter("vote =", 1).count()
                count = up_votes - down_votes

                issue.update(up_votes=up_votes,
                             down_votes=down_votes,
                             count=count)

        # Write out the results.
        template_params.update(issues=git_data,
                               error=err_msg
                               )

        template = env.get_template('feedback.html')
        html = template.render(template_params)
        self.response.out.write(html)

    @authenticate
    def post(self, user):

        # This should never happen, because voting
        # links are disabled for non-logged-in users.

        # Get the data from the ajax call.
        issue_id = int(self.request.get('id'))
        up = self.request.get('up')
        down = self.request.get('down')

        # Set our vote flag to record the user's opinion.
        if up == 'true':
            issue_status = 1
        elif down == 'true':
            issue_status = -1
        else:
            issue_status = 0

        # Put it in the database.
        issue = Issue.all().ancestor(user).filter("issue_id =",
                                                  issue_id).get()
        issue.vote = issue_status
        issue.put()

        # TODO log in the activity log


class PricingHandler(ModelrPageRequest):
    def get(self):

        user = self.verify()
        template_params = self.get_base_params(user=user)
        template = env.get_template('pricing.html')
        html = template.render(template_params)
        activity = "pricing"

        if user:
            ActivityLog(user_id=user.user_id,
                        activity=activity,
                        parent=ModelrParent.all().get()).put()

        self.response.out.write(html)


class HelpHandler(ModelrPageRequest):
    def get(self, subpage):

        if subpage:
            page = subpage
        else:
            page = 'help'
        page += '.html'

        user = self.verify()
        template_params = self.get_base_params(user=user)
        template = env.get_template(page)
        html = template.render(template_params)
        activity = "help"

        if user:
            ActivityLog(user_id=user.user_id,
                        activity=activity,
                        parent=ModelrParent.all().get()).put()

        self.response.out.write(html)

    def post(self, subpage):

        email = self.request.get('email')
        message = self.request.get('message')

        user = self.verify()

        try:
            send_message("User message %s" % email, message)
            template = env.get_template('message.html')
            msg = ("Thank you for your message. " +
                   "We'll be in touch shortly.")
            html = template.render(success=msg, user=user)
            self.response.out.write(html)

        except:
            template = env.get_template('message.html')
            msg = ('Your message was not sent.&nbsp;&nbsp; ' +
                   '<button class="btn btn-default" ' +
                   'onclick="goBack()">Go back and retry</button>')
            html = template.render(warning=msg, user=user)
            self.response.out.write(html)


class TermsHandler(ModelrPageRequest):
    def get(self):

        user = self.verify()
        template_params = self.get_base_params(user=user)
        template = env.get_template('terms.html')
        html = template.render(template_params)
        activity = "terms"

        if user:
            ActivityLog(user_id=user.user_id,
                        activity=activity,
                        parent=ModelrParent.all().get()).put()

        self.response.out.write(html)


class PrivacyHandler(ModelrPageRequest):
    def get(self):

        user = self.verify()
        template_params = self.get_base_params(user=user)
        template = env.get_template('privacy.html')
        html = template.render(template_params)
        activity = "privacy"

        if user:
            ActivityLog(user_id=user.user_id,
                        activity=activity,
                        parent=ModelrParent.all().get()).put()

        self.response.out.write(html)


class ProfileHandler(ModelrPageRequest):

    @authenticate
    def get(self, user):

        groups = []
        for group in user.group:
            g = Group.all().ancestor(ModelrParent.all().get())\
                           .filter("name =", group)
            g = g.fetch(1)
            if g:
                groups.append(g[0])

        template_params = self.get_base_params(user=user, groups=groups,
                                               stripe_key=stripe_public_key)

        if self.request.get("createfailed"):
            create_error = "Group name exists"
            template_params.update(create_error=create_error)
        if self.request.get("joinfailed"):
            join_error = "Group does not exists"
            template_params.update(join_error=join_error)

        # Get the user permission requests
        req = GroupRequest.all().ancestor(ModelrParent.all().get())\
                                .filter("user =", user.user_id)
        if req:
            template_params.update(requests=req)

        # Get the users adminstrative requests
        admin_groups = Group.all().ancestor(ModelrParent.all().get())\
                                  .filter("admin =", user.user_id)
        admin_groups = admin_groups.fetch(100)
        req = []
        for group in admin_groups:
            # Check for a request
            g_req = GroupRequest.all().ancestor(ModelrParent.all().get())
            g_req = g_req.filter("group =", group.name).fetch(100)
            req = req + [{'group': group.name,
                          'user': User.all().filter("user_id =", i.user).get()}
                         for i in g_req]

        template_params.update(admin_req=req)
        template = env.get_template('profile.html')
        html = template.render(template_params)

        activity = "profile_view"
        ActivityLog(user_id=user.user_id,
                    activity=activity,
                    parent=ModelrParent.all().get()).put()
        self.response.out.write(html)

    @authenticate
    def post(self, user):

        err_string = []
        # Join a group
        join_group = self.request.get("join_group")
        if join_group:
            activity = "joined_group"
            ActivityLog(user_id=user.user_id,
                        activity=activity,
                        parent=ModelrParent.all().get()).put()
            try:
                group = Group.all().ancestor(ModelrParent.all().get())
                group = group.filter("name =", join_group).fetch(1)[0]
                if user.user_id in group.allowed_users:
                    if group.name not in user.group:
                        user.group.append(group.name)
                        user.put()
                else:
                    GroupRequest(user=user.user_id,
                                 group=group.name,
                                 parent=ModelrParent.all().get()).put()

            except IndexError:
                err_string.append("joinfailed=1")

        # Leave a group
        group = self.request.get("selected_group")
        if group in user.group:
            activity = "left_group"
            ActivityLog(user_id=user.user_id,
                        activity=activity,
                        parent=ModelrParent.all().get()).put()
            user.group.remove(group)
            user.put()

        # Create a group
        group = self.request.get("create_group")

        if group:
            if not Group.all().ancestor(ModelrParent.all().get())\
                              .filter("name =", group).fetch(1):
                Group(name=group, admin=user.user_id,
                      allowed_users=[user.user_id],
                      parent=ModelrParent.all().get()).put()
                user.group.append(group)
                user.put()
                activity = "created_group"
                ActivityLog(user_id=user.user_id,
                            activity=activity,
                            parent=ModelrParent.all().get()).put()
            else:
                err_string.append("createfailed=1")

        # Handle a group request
        request_user = self.request.get("request_user")
        if request_user:
            user_id = int(request_user)
            group = self.request.get("request_group")
            if self.request.get("allow") == "True":
                u = User.all().ancestor(ModelrParent.all().get())
                u = u.filter("user_id =", user_id).fetch(1)
                if u:
                    u[0].group.append(group)
                    g = Group.all().ancestor(ModelrParent.all().get())
                    g = g.filter("name =", group).fetch(1)[0]
                    g.allowed_users.append(u[0].user_id)
                    u[0].put()
                    g.put()
            activity = "request_response"
            ActivityLog(user_id=user.user_id,
                        activity=activity,
                        parent=ModelrParent.all().get()).put()

            g_req = GroupRequest.all().ancestor(ModelrParent.all().get())
            g_req = g_req.filter("user =", user_id)
            g_req = g_req.filter("group =", group).fetch(100)
            for g in g_req:
                g.delete()

        err_string = '&'.join(err_string) if err_string else ''
        self.redirect('/profile?' + err_string)


class SettingsHandler(ModelrPageRequest):

    @authenticate
    def get(self, user):

        template_params = self.get_base_params(user=user)
        template = env.get_template('settings.html')
        html = template.render(template_params)
        self.response.out.write(html)


class ForgotHandler(webapp2.RequestHandler):
    """
    Class for forgotten passwords
    """

    def get(self):
        template = env.get_template('forgot.html')
        html = template.render()
        self.response.out.write(html)

    def post(self):

        email = self.request.get('email')
        template = env.get_template('message.html')

        try:
            forgot_password(email, parent=ModelrParent.all().get())

            msg = ("Please check your inbox and spam folder " +
                   "for our message. Then click on the link " +
                   "in the email.")
            html = template.render(success=msg)
            self.response.out.write(html)
        except AuthExcept as e:
            html = template.render(error=e.msg)
            self.response.out.write(html)


class ResetHandler(ModelrPageRequest):
    """
    Class for resetting passwords
    """

    @authenticate
    def post(self, user):
        current_pword = self.request.get("current_pword")
        new_password = self.request.get("new_password")
        verify = self.request.get("verify")

        template = env.get_template('profile.html')

        try:
            reset_password(user, current_pword, new_password,
                           verify)
            msg = ("You reset your password.")
            html = template.render(user=user, success=msg)
            self.response.out.write(html)
        except AuthExcept as e:
            html = template.render(user=user, error=e.msg)


class DeleteHandler(ModelrPageRequest):
    """
    Class for deleting account

    There is some placeholder code below, and
    also see delete_account() in ModAuth.py

    Steps:
    1. Ask user if they are sure (Bootstrap modal in JS?)
       http://stackoverflow.com/questions/8982295/confirm-delete-modal-dialog-with-twitter-bootstrap
    2. Suspend Subscription with delete method in Stripe,
       using at_period_end=True (note, this is NOT the default)
       Docs > https://stripe.com/docs/api#cancel_subscription
    3. Remove them from MailChimp customer list
       Docs > http://apidocs.mailchimp.com/api/2.0/lists/unsubscribe.php
    4. Give them some confirmation by email?
       Some code in bogus function to do this now

    """

    @authenticate
    def post(self, user):

        template = env.get_template('message.html')

        try:
            cancel_subscription(user)
            msg = "Unsubscribed from Modelr"
            html = template.render(user=user, msg=msg)
            self.response.write(html)

        except AuthExcept as e:
            html = template.render(user=user, error=e.msg)
            self.response.write(html)


class SignUp(webapp2.RequestHandler):
    """
    Class for registering users
    """

    def get(self):

        template = env.get_template('signup.html')
        error = self.request.get("error")
        if error == 'auth_failed':
            error_msg = "failed to authorize user"
            html = template.render(error=error_msg)
        else:
            html = template.render()

        self.response.out.write(html)

    def post(self):

        email = self.request.get('email')
        password = self.request.get('password')
        verify = self.request.get('verify')

        if password != verify:
            template = env.get_template('signup.html')
            msg = "Password mismatch"
            html = template.render(email=email,
                                   error=msg)
            self.response.out.write(html)

        else:
            try:
                signup(email, password,
                       parent=ModelrParent.all().get())

                # Show the message page with "Success!"
                template = env.get_template('message.html')
                msg = ("Please check your inbox and spam folder " +
                       "for our message. Then click on the link " +
                       "in the email.")
                html = template.render(success=msg)
                self.response.out.write(html)

            except AuthExcept as e:
                template = env.get_template('signup.html')
                msg = e.msg
                html = template.render(email=email,
                                       error=msg)
                self.response.out.write(html)


class EmailAuthentication(ModelrPageRequest):
    """
    This is where billing and user account creation takes place
    """

    def get(self):

        user_id = self.request.get("user_id")

        try:
            # Change this to check the user can be validated and
            # get temp_user
            user = verify_signup(user_id, ModelrParent.all().get())

        except AuthExcept:
            self.redirect('/signup?error=auth_failed')
            return

        msg = "Thank you for verifying your email address."
        params = self.get_base_params(user=user,
                                      stripe_key=stripe_public_key)
        template = env.get_template('checkout.html')
        html = template.render(params, success=msg)
        self.response.out.write(html)

    def post(self):
        """
        Adds the user to the stripe customer list
        """
        email = self.request.get('stripeEmail')
        price = PRICE # set at head of this file

        # Secret API key for Canada Post postal lookup
        cp_prod = "3a04462597330c85:46c19862981c734ff8f7b2"
        # cp_dev = "09b48e3a40e710ed:bb6f209fdecff9af3ec10d"
        cp_key = base64.b64encode(cp_prod)

        # Get the credit card details submitted by the form
        token = self.request.get('stripeToken')

        # Create the customer account
        try:
            customer = stripe.Customer\
                             .create(card=token,
                                     email=email,
                                     description="New Modelr customer")
        except:
            # The card has been declined
            # Let the user know and DON'T UPGRADE USER
            self.redirect('/signin?verified=false')
            return

        # Check the country to see if we need to charge tax
        country = self.request.get('stripeBillingAddressCountry')
        if country == "Canada":

            # Get postal code for canada post request
            postal_code = self.request.get('stripeBillingAddressZip')\
                                      .replace(" ", "")

            # Hook up to the web api
            params = urllib.urlencode({"d2po": "True",
                                       "postalCode": postal_code,
                                       "maximum": 1})
            cp_url = ("https://soa-gw.canadapost.ca/rs/postoffice?%s"
                      % params)

            headers = {"Accept": "application/vnd.cpc.postoffice+xml",
                       "Authorization": "Basic " + cp_key}

            try:
                req = urllib2.Request(cp_url, headers=headers)
                result = urllib2.urlopen(req).read()
                xml_root = ElementTree.fromstring(result)

                # This is super hacky, but the only way I could get the
                # XML out
                province = []
                for i in xml_root.iter('{http://www.canadapost.ca/ws/' +
                                       'postoffice}province'):
                    province.append(i.text)
                    tax_code = province[0]

                tax = tax_dict.get(tax_code) * price

                # Add the tax to the invoice
                stripe.InvoiceItem.create(customer=customer.id,
                                          amount=int(tax),
                                          currency="usd",
                                          description="Canadian Taxes")

            except:

                send_message(subject="taxation failed for %s" % customer.id)
                tax = 0

        else:
            tax_code = country
            tax = 0

        # Create the charge on Stripe's servers -
        # this will charge the user's card
        try:
            customer.subscriptions.create(plan="Monthly")
        except:
            # The card has been declined
            # Let the user know and DON'T UPGRADE USER
            self.redirect('/signin?verified=false')
            return

        # get the temp user from the database
        try:
            initialize_user(email, customer.id,
                            ModelrParent.all().get(),
                            tax_code, price, tax)
        except:

            send_message(subject="Registration Failed",
                         message=("Failed to register user %s to " +
                                  "Modelr but was billed by Stripe. " +
                                  "Customer ID: %s") % (email, customer.id))
            self.redirect('/signin?verified=false')
            raise

        self.redirect('/signin?verified=true')


class SignIn(webapp2.RequestHandler):

    def get(self):

        status = self.request.get("verified")
        redirect = self.request.get('redirect')

        if status == "true":
            msg = ("Your account has been created and your card has "
                   "been charged. Welcome to Modelr!")
            error_msg = None

        elif status == "false":
            error_msg = ("Failed to create account. Your credit card will "
                         "not be charged.")
            msg = None
        else:
            msg = None
            error_msg = None

        template = env.get_template('signin.html')
        html = template.render(success=msg, error=error_msg,
                               redirect=redirect)
        self.response.out.write(html)

    def post(self):

        email = self.request.get('email')
        password = self.request.get('password')
        redirect = self.request.get('redirect').encode('utf-8')

        try:
            signin(email, password, ModelrParent.all().get())
            cookie = get_cookie_string(email)
            self.response.headers.add_header('Set-Cookie', cookie)

            if redirect:
                self.redirect(redirect)
            else:
                self.redirect('/')

        except AuthExcept as e:
            template = env.get_template('signin.html')
            msg = e.msg
            html = template.render(email=email,
                                   error=msg)
            self.response.out.write(html)


class SignOut(ModelrPageRequest):

    @authenticate
    def get(self, user):

        activity = "signout"
        ActivityLog(user_id=user.user_id,
                    activity=activity,
                    parent=ModelrParent.all().get()).put()
        self.response.headers.add_header('Set-Cookie',
                                         'user=""; Path=/')
        self.redirect('/')


class ManageGroup(ModelrPageRequest):
    """
    Manages and administrates group permissions
    """

    @authenticate
    def get(self, user):

        group_name = self.request.get("selected_group")

        group = Group.all().ancestor(ModelrParent.all().get())
        group = group.filter("name =", group_name).fetch(1)
        if (not group):
            self.redirect('/profile')
            return

        group = group[0]
        if group.admin != user.user_id:
            self.redirect('/profile')
            return

        users = []
        for user_id in group.allowed_users:
            u = User.all().ancestor(ModelrParent.all().get())\
                          .filter("user_id =", user_id)
            u = u.fetch(1)
            if u:
                users.append(u[0])

        params = self.get_base_params(user=user, users=users,
                                      group=group)
        template = env.get_template('manage_group.html')
        html = template.render(params)

        activity = "manage_group"
        ActivityLog(user_id=user.user_id,
                    activity=activity,
                    parent=ModelrParent.all().get()).put()
        self.response.out.write(html)

    @authenticate
    def post(self, user):
        group_name = self.request.get("group")
        group = Group.all().ancestor(ModelrParent.all().get())
        group = group.filter("name =", group_name).fetch(1)[0]

        # remove a user
        rm_user = self.request.get("user")

        if rm_user:
            u = User.all().ancestor(ModelrParent.all().get())
            u = u.filter("user_id =", int(rm_user)).fetch(1)

            if u and group_name in u[0].group:
                u[0].group.remove(group_name)
                u[0].put()
                group.allowed_users.remove(int(rm_user))
                group.put()
            self.redirect('/manage_group?selected_group=%s'
                          % group.name)

            activity = "removed_user"
            ActivityLog(user_id=user.user_id,
                        activity=activity,
                        parent=ModelrParent.all().get()).put()
            return

        # abolish a group
        if (self.request.get("abolish") == "abolish"):
            for uid in group.allowed_users:
                u = User.all().ancestor(ModelrParent.all().get())
                u = u.filter("user_id =", uid).fetch(1)
                if u and group.name in u[0].group:
                    u[0].group.remove(group.name)
                    u[0].put()
            group.delete()
            activity = "abolished_group"
            ActivityLog(user_id=user.user_id,
                        activity=activity,
                        parent=ModelrParent.all().get()).put()
            self.redirect('/profile')
            return


class ModelBuilder(ModelrPageRequest):

    @authenticate
    def get(self, user):

        params = self.get_base_params(user=user)
        template = env.get_template('model_builder.html')
        html = template.render(params)
        self.response.out.write(html)

    @authenticate
    def post(self, user):

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('All OK!!')

        bucket = '/modelr_live_bucket/'
        filename = bucket + str(user.user_id) + '/' + str(time.time())

        encoded_image = self.request.get('image').split(',')[1]
        pic = base64.b64decode(encoded_image)

        gcsfile = gcs.open(filename, 'w')
        gcsfile.write(pic)

        gcsfile.close()

        bs_file = '/gs' + filename

        blob_key = blobstore.create_gs_key(bs_file)

        ImageModel(parent=user,
                   user=user.user_id,
                   image=blob_key).put()
        # TODO Logging


class ModelHandler(ModelrPageRequest):

    @authenticate
    def get(self, user):

        # Make the upload url
        upload_url = blobstore.create_upload_url('/upload')

        # Get the model images
        models = ImageModel.all().ancestor(user).order("-date")
        models = models.fetch(100)

        # Get the default models
        admin_user = User.all().filter("user_id =", admin_id).get()
        if user.user_id != admin_id:
            default_models = ImageModel.all().ancestor(admin_user).fetch(100)
        else:
            default_models = []
            
        all_models = set(models + default_models)
        
        # Create the serving urls
        imgs = [images.get_serving_url(i.image, size=1400,
                                       crop=False, secure_url=True)
                for i in all_models]

        keys = [str(i.key()) for i in all_models]

        # Read in each image to get the RGB colours
        readers = [blobstore.BlobReader(i.image.key())
                   for i in (models + default_models)]
        colors = [[RGBToString(j[1])
                   for j in Image.open(i).convert('RGB').getcolors()]
                  for i in readers]

        # Grab the rocks
        rocks = Rock.all()
        rocks.ancestor(user)
        rocks.filter("user =", user.user_id)
        rocks.order("-date")

        default_rocks = Rock.all()
        default_rocks.filter("user =", admin_id)
        params = self.get_base_params(user=user,
                                      images=imgs,
                                      colors=colors,
                                      keys=keys,
                                      rocks=rocks.fetch(100),
                                      default_rocks=default_rocks.fetch(100),
                                      upload_url=upload_url)

        # Check if there was an upload error (see Upload handler)
        if self.request.get("error"):
            params.update(error="Invalid image file")

        template = env.get_template('model2.html')
        html = template.render(params)
        self.response.out.write(html)


class NotFoundPageHandler(ModelrPageRequest):
    def get(self):
        self.error(404)
        template = env.get_template('404.html')
        html = template.render()
        self.response.out.write(html)


class AdminHandler(ModelrPageRequest):

    @authenticate
    def get(self, user):

        if "admin" not in user.group:
            self.redirect('/')

        template = env.get_template('admin_site.html')
        html = template.render(self.get_base_params(user=user))
        self.response.out.write(html)

    @authenticate
    def post(self, user):
        if "admin" not in user.group:
            self.redirect('/')

        template = env.get_template('admin_site.html')

        host = self.request.get('host')
        if (len(host) > 0):
            server = Server.all().ancestor(ModelrParent.all().get()).get()
            server.host = self.request.get('host')
            server.put()
            html = template.render(
                self.get_base_params(success="Updated Host"))
            self.response.write(html)
            return

        email = self.request.get('email')
        password = self.request.get('password')
        verify = self.request.get('verify')

        if (len(email) > 0):
            if password != verify:
                template = env.get_template('admin_site.html')
                msg = "Password mismatch"
                html = template.render(email=email,
                                       error=msg)
                self.response.out.write(html)
                return

            else:
                try:
                    make_user(email=email,
                              password=password,
                              parent=ModelrParent.all().get())
                    template = env.get_template('admin_site.html')
                    html = template.render(success="Added User",
                                           email=email, user=user)
                    self.response.out.write(html)
                    return

                except AuthExcept as e:
                    template = env.get_template('admin_site.html')
                    html = template.render(error=e.msg, user=user,
                                           email=email)
                    self.response.out.write(html)
                    return

        else:
            template = env.get_template('admin_site.html')
            html = template.render()
            self.response.out.write(html)


class FixModels(ModelrPageRequest):

    def get(self):

        models = EarthModel.all().fetch(1000)

        for m in models:

            print m.name
            data = json.loads(m.data)
            cmap = data["mapping"]

            for color, rock_data in cmap.iteritems():

                rock_name = rock_data["name"]

                try:
                    rocks = Rock.all().ancestor(
                        ModelrParent.all().get())

                    rock = rocks.filter("name =", rock_name).get()
                    cmap[color]["db_key"] = str(rock.key())
                    
                except:
                    pass
            m.data = json.dumps(data).encode()
        self.response.write("OK")


class FixDefaultRocks(ModelrPageRequest):
    # Used to fix rocks in the database
    def get(self):

        from default_rocks import default_rocks
        ModelrRoot = ModelrParent.all().get()
        admin_user = User.all().ancestor(ModelrRoot).filter("user_id =",
                                                            admin_id).get()
        for i in default_rocks:

            rocks = Rock.all()
            rocks.filter("user =", admin_id)
            rocks.filter("name =", i['name'])
            rocks = rocks.fetch(100)

            for r in rocks:
                r.delete()

            rock = Rock(parent=admin_user)
            rock.user = admin_id
            rock.name = i['name']
            rock.group = 'public'

            rock.description = i['description']

            rock.vp = float(i['vp'])
            rock.vs = float(i['vs'])
            rock.rho = float(i['rho'])

            rock.vp_std = float(i['vp_std'])
            rock.vs_std = float(i['vs_std'])
            rock.rho_std = float(i['rho_std'])

            rock.Parent = admin_user
            rock.put()
        self.response.out.write("oK")


class ServerError(ModelrPageRequest):

    def post(self):

        send_message("Server Down", "Scripts did not populate")


class Model1DHandler(ModelrPageRequest):

    @authenticate
    def get(self, user):

        all_rocks = get_all_items_user(Rock, user)

        rock_json = json.dumps([rock.json for rock in all_rocks])
      
        all_fluids = get_all_items_user(Fluid, user)
        fluid_json = json.dumps([fluid.json for fluid in all_fluids])

        colour_map = {item.name: RGBToString(colour)
                      for (item, colour) in
                      zip(all_rocks + all_fluids, usgs_colours)}

        colour_map = json.dumps(colour_map)
        params = self.get_base_params(user=user,
                                      db_rocks=rock_json,
                                      db_fluids=fluid_json,
                                      colour_map=colour_map)

        template = env.get_template('1D_model.html')

        html = template.render(params)
        self.response.write(html)
