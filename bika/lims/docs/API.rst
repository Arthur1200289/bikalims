=============
Bika LIMS API
=============

The Bika LIMS API provides single functions for single purposes.
This Test builds completely on the API without any further imports needed.


API
===

The purpose of this API is to help coders to follow the DRY principle (Don't
Repeat Yourself). It also ensures that the most effective and efficient method is
used to achieve a task.

Import it first::

    >>> from bika.lims import api


Getting the Portal
------------------

The Portal is the Bika LIMS root object::

    >>> portal = api.get_portal()
    >>> portal
    <PloneSite at /plone>


Getting the Bika Setup object
-----------------------------

The Bika Setup object gives access to all of the Bika configuration settings::

    >>> bika_setup = api.get_bika_setup()
    >>> bika_setup
    <BikaSetup at /plone/bika_setup>


Creating new Content
--------------------

Creating new contents in Bika LIMS requires some special knowledge.
This function helps to do it right and creates a content for you.

Here we create a new `Client` in the `plone/clients` folder::

    >>> client = api.create(portal.clients, "Client", title="Test Client")
    >>> client
    <Client at /plone/clients/client-1>

     >>> client.Title()
     'Test Client'


Getting a Tool
--------------

There are many ways to get a tool in Bika LIMS / Plone. This function
centralizes this functionality and makes it painless::

    >>> api.get_tool("bika_setup_catalog")
    <BikaSetupCatalog at /plone/bika_setup_catalog>

Trying to fetch an non-existing tool raises a custom `BikaLIMSError`.

    >>> api.get_tool("NotExistingTool")
    Traceback (most recent call last):
    [...]
    BikaLIMSError: No tool named 'NotExistingTool' found.

This error can also be used for custom methods with the `fail` function::

    >>> api.fail("This failed badly")
    Traceback (most recent call last):
    [...]
    BikaLIMSError: This failed badly


Getting an Object
-----------------

Getting a tool from a catalog brain is a common task in Bika LIMS. This function
provides an unified interface to portal objects **and** brains.
Furthermore it is idempotent, so it can be called multiple times in a row::

We will demonstrate the usage on the client object we created above::

    >>> api.get_object(client)
    <Client at /plone/clients/client-1>

    >>> api.get_object(api.get_object(client))
    <Client at /plone/clients/client-1>

Now we show it with catalog results::

    >>> portal_catalog = api.get_tool("portal_catalog")
    >>> brains = portal_catalog(portal_type="Client")
    >>> brains
    [<Products.ZCatalog.Catalog.mybrains object at 0x...>]

    >>> brain = brains[0]

    >>> api.get_object(brain)
    <Client at /plone/clients/client-1>

    >>> api.get_object(api.get_object(brain))
    <Client at /plone/clients/client-1>

No supported objects raise an error::

    >>> api.get_object(object())
    Traceback (most recent call last):
    [...]
    BikaLIMSError: <object object at 0x...> is not supported.


Checking if an Object is the Portal
-----------------------------------

Sometimes it can be handy to check if the current object is the portal::

    >>> api.is_portal(portal)
    True

    >>> api.is_portal(client)
    False

    >>> api.is_portal(object())
    False


Checking if an Object is a Catalog Brain
----------------------------------------

Knowing if we have an object or a brain can be handy. This function checks this for you::

    >>> api.is_brain(brain)
    True

    >>> api.is_brain(api.get_object(brain))
    False

    >>> api.is_brain(object())
    False


Checking if an Object is a Dexterity Content
--------------------------------------------

This function checks if an object is a `Dexterity` content type::

    >>> api.is_dexterity_content(client)
    False

    >>> api.is_dexterity_content(portal)
    False

We currently have no `Dexterity` contents, so testing this comes later...


Checking if an Object is an AT Content
--------------------------------------

This function checks if an object is an `Archetypes` content type::

    >>> api.is_at_content(client)
    True

    >>> api.is_at_content(portal)
    False

    >>> api.is_at_content(object())
    False


Getting the Schema of a Content
-------------------------------

The schema contains the fields of a content object. Getting the schema is a
common task, but differs between `ATContentType` based objects and `Dexterity`
based objects. This function brings it under one umbrella::

    >>> schema = api.get_schema(client)
    >>> schema
    <Products.Archetypes.Schema.Schema object at 0x...>

Catalog brains are also supported::

    >>> api.get_schema(brain)
    <Products.Archetypes.Schema.Schema object at 0x...>


Getting the Fields of a Content
-------------------------------

The fields contain all the values that an object holds and are therefore
responsible for getting and setting the information.

This function returns the fields as a dictionary mapping of `{"key": value}`::

    >>> fields = api.get_fields(client)
    >>> fields.get("ClientID")
    <Field ClientID(string:rw)>

Catalog brains are also supported::

    >>> api.get_fields(brain).get("ClientID")
    <Field ClientID(string:rw)>


Getting the ID of a Content
---------------------------

Getting the ID is a common task in Bika LIMS.
This function takes care that catalog brains are not waked up for this task::

    >>> api.get_id(portal)
    'plone'

    >>> api.get_id(client)
    'client-1'

    >>> api.get_id(brain)
    'client-1'


Getting the Title of a Content
------------------------------

Getting the Title is a common task in Bika LIMS.
This function takes care that catalog brains are not waked up for this task::

    >>> api.get_title(portal)
    u'Plone site'

    >>> api.get_title(client)
    'Test Client'

    >>> api.get_title(brain)
    'Test Client'


Getting the Description of a Content
------------------------------------

Getting the Description is a common task in Bika LIMS.
This function takes care that catalog brains are not waked up for this task::

    >>> api.get_description(portal)
    ''

    >>> api.get_description(client)
    ''

    >>> api.get_description(brain)
    ''


Getting the UID of a Content
----------------------------

Getting the UID is a common task in Bika LIMS.
This function takes care that catalog brains are not waked up for this task.

The portal object actually has no UID. This funciton defines it therfore to be `0`::

    >>> api.get_uid(portal)
    '0'

    >>> uid_client = api.get_uid(client)
    >>> uid_client_brain = api.get_uid(brain)
    >>> uid_client is uid_client_brain
    True


Getting the URL of a Content
----------------------------

Getting the URL is a common task in Bika LIMS.
This function takes care that catalog brains are not waked up for this task::

    >>> api.get_url(portal)
    'http://nohost/plone'

    >>> api.get_url(client)
    'http://nohost/plone/clients/client-1'

    >>> api.get_url(brain)
    'http://nohost/plone/clients/client-1'


Getting the Icon of a Content
-----------------------------

    >>> api.get_icon(client)
    '<img width="16" height="16" src="http://nohost/plone/++resource++bika.lims.images/client.png" title="Test Client" />'

    >>> api.get_icon(brain)
    '<img width="16" height="16" src="http://nohost/plone/++resource++bika.lims.images/client.png" title="Test Client" />'

    >>> api.get_icon(client, html_tag=False)
    'http://nohost/plone/++resource++bika.lims.images/client.png'

    >>> api.get_icon(client, html_tag=False)
    'http://nohost/plone/++resource++bika.lims.images/client.png'


Getting an object by UID
------------------------

This function finds an object by its uinique ID (UID).
The portal object with the defined UId of `0` is also supported::

    >>> api.get_object_by_uid('0')
    <PloneSite at /plone>

    >>> api.get_object_by_uid(uid_client)
    <Client at /plone/clients/client-1>

    >>> api.get_object_by_uid(uid_client_brain)
    <Client at /plone/clients/client-1>


Getting an object by Path
-------------------------

This function finds an object by its physical path::

    >>> api.get_object_by_path('/plone')
    <PloneSite at /plone>

    >>> api.get_object_by_path('/plone/clients/client-1')
    <Client at /plone/clients/client-1>

Paths outside the portal raise an error::

    >>> api.get_object_by_path('/root')
    Traceback (most recent call last):
    [...]
    BikaLIMSError: Not a physical path inside the portal.


Getting the Physical Path of an Object
--------------------------------------

The physical path describes exactly where an object is located inside the portal.
This function unifies the different approaches to get the physical path and does
so in the most efficient way::

    >>> api.get_path(portal)
    '/plone'

    >>> api.get_path(client)
    '/plone/clients/client-1'

    >>> api.get_path(brain)
    '/plone/clients/client-1'

    >>> api.get_path(object())
    Traceback (most recent call last):
    [...]
    BikaLIMSError: <object object at 0x...> is not supported.


Getting the Physical Parent Path of an Object
---------------------------------------------

This function returns the physical path of the parent object::

    >>> api.get_parent_path(client)
    '/plone/clients'

    >>> api.get_parent_path(brain)
    '/plone/clients'

However, this function goes only up to the portal object::

    >>> api.get_parent_path(portal)
    '/plone'

Like with the other functions, only portal objects are supported::

    >>> api.get_parent_path(object())
    Traceback (most recent call last):
    [...]
    BikaLIMSError: <object object at 0x...> is not supported.


Getting the Parent Object
-------------------------

This function returns the parent object::

    >>> api.get_parent(client)
    <ClientFolder at /plone/clients>

Brains are also supported::

    >>> api.get_parent(brain)
    <ClientFolder at /plone/clients>

The function can also use a catalog query on the `portal_catalog` and return a
brain, if the passed parameter `catalog_search` was set to true. ::

    >>> api.get_parent(client, catalog_search=True)
    <Products.ZCatalog.Catalog.mybrains object at 0x...>

    >>> api.get_parent(brain, catalog_search=True)
    <Products.ZCatalog.Catalog.mybrains object at 0x...>

However, this function goes only up to the portal object::

    >>> api.get_parent(portal)
    <PloneSite at /plone>

Like with the other functions, only portal objects are supported::

    >>> api.get_parent(object())
    Traceback (most recent call last):
    [...]
    BikaLIMSError: <object object at 0x...> is not supported.


Searching Objects
-----------------

Searching in Bika LIMS requires knowledge in which catalog the object is indexed.
This function unifies all Bika LIMS catalog to a single search interface::

    >>> results = api.search({'portal_type': 'Client'})
    >>> results
    [<Products.ZCatalog.Catalog.mybrains object at 0x...>]

Multiple content types are also supported::

    >>> results = api.search({'portal_type': ['Client', 'ClientFolder'], 'sort_on': 'getId'})
    >>> map(api.get_id, results)
    ['client-1', 'clients']

Now we create some objects which are located in the `bika_setup_catalog`::

    >>> instruments = bika_setup.bika_instruments
    >>> instrument1 = api.create(instruments, "Instrument", title="Instrument-1")
    >>> instrument2 = api.create(instruments, "Instrument", title="Instrument-2")
    >>> instrument3 = api.create(instruments, "Instrument", title="Instrument-3")

    >>> results = api.search({'portal_type': 'Instrument', 'sort_on': 'getId'})
    >>> len(results)
    3

    >>> map(api.get_id, results)
    ['instrument-1', 'instrument-2', 'instrument-3']

If a query requires to search in **multiple catalogs**, the results get merged
after each search and sorted afterwards::

    >>> results = api.search({'portal_type': ['Client', 'ClientFolder', 'Instrument'], 'sort_on': 'getId'})
    >>> len(results)
    5
    >>> map(api.get_id, results)
    ['client-1', 'clients', 'instrument-1', 'instrument-2', 'instrument-3']

It is also possible to limit the results::

    >>> results = api.search({'portal_type': ['Client', 'ClientFolder', 'Instrument'], 'sort_on': 'getId', 'limit': 2})
    >>> len(results)
    2
    >>> map(api.get_id, results)
    ['client-1', 'clients']

We can also specify explicit catalogs to search::

    >>> analysiscategories = bika_setup.bika_analysiscategories
    >>> analysiscategory1 = api.create(analysiscategories, "AnalysisCategory", title="AC-1")
    >>> analysiscategory2 = api.create(analysiscategories, "AnalysisCategory", title="AC-2")
    >>> analysiscategory3 = api.create(analysiscategories, "AnalysisCategory", title="AC-3")

Because if we don't specify the `portal_type`, the catalog defaults to the
`portal_catalog`, which will not find this item::

    >>> results = api.search({"id": "analysiscategory-1"})
    >>> len(results)
    0

Would we add the `portal_type`, the search function would ask the
`archetype_tool` for the right catalog, and it would return a result::

    >>> results = api.search({"portal_type": "AnalysisCategory", "id": "analysiscategory-1"})
    >>> len(results)
    1

We could also explicitly define a catalog to achieve the same::

    >>> results = api.search({"id": "analysiscategory-1"}, catalog="bika_setup_catalog")
    >>> len(results)
    1


Getting an Attribute of an Object
---------------------------------

This function handles attributes and methods the same and returns their value.
It also handles security and is able to return a default value instead of
raising an `Unauthorized` error::

    >>> uid_brain = api.safe_getattr(brain, "UID")
    >>> uid_obj = api.safe_getattr(client, "UID")

    >>> uid_brain == uid_obj
    True

    >>> api.safe_getattr(brain, "review_state")
    'active'

    >>> api.safe_getattr(brain, "NONEXISTING")
    Traceback (most recent call last):
    [...]
    BikaLIMSError: Attribute 'NONEXISTING' not found.

    >>> api.safe_getattr(brain, "NONEXISTING", "")
    ''

Getting the Portal Catalog
--------------------------

This tool is needed so often, that this function just returns it::

    >>> api.get_portal_catalog()
    <CatalogTool at /plone/portal_catalog>


Getting the Review History of an Object
---------------------------------------

The review history gives information about the objects' workflow changes::

    >>> review_history = api.get_review_history(client)
    >>> sorted(review_history[0].items())
    [('action', None), ('actor', 'test_user_1_'), ('comments', ''), ('review_state', 'active'), ('time', DateTime('...'))]


Getting the Revision History of an Object
-----------------------------------------

The review history gives information about the objects' workflow changes::

    >>> revision_history = api.get_revision_history(client)
    >>> sorted(revision_history[0])
    ['action', 'actor', 'actor_home', 'actorid', 'comments', 'review_state', 'state_title', 'time', 'transition_title', 'type']
    >>> revision_history[0]["transition_title"]
    u'Create'


Getting the assigned Workflows of an Object
-------------------------------------------

This function returns all assigned workflows for a given object::

    >>> api.get_workflows_for(bika_setup)
    ('bika_one_state_workflow',)

    >>> api.get_workflows_for(client)
    ('bika_one_state_workflow', 'bika_inactive_workflow')


Getting the Workflow Status of an Object
----------------------------------------

This function returns the state of a given object::

    >>> api.get_workflow_status_of(client)
    'active'


Getting the granted Roles for a certain Permission on an Object
---------------------------------------------------------------

This function returns a list of Roles, which are granted the given Permission
for the passed in object::

    >>> api.get_roles_for_permission("Modify portal content", bika_setup)
    ['LabManager', 'Manager']



Checking if an Object is Versionable
------------------------------------

Some contents in Bika LIMS support versioning. This function checks this for you.

Instruments are not versionable::

    >>> api.is_versionable(instrument1)
    False

Analysisservices are versionable::

    >>> analysisservices = bika_setup.bika_analysisservices
    >>> analysisservice1 = api.create(analysisservices, "AnalysisService", title="AnalysisService-1")
    >>> analysisservice2 = api.create(analysisservices, "AnalysisService", title="AnalysisService-2")
    >>> analysisservice3 = api.create(analysisservices, "AnalysisService", title="AnalysisService-3")

    >>> api.is_versionable(analysisservice1)
    True


Getting the Version of an Object
--------------------------------

This function returns the version as an integer::

    >>> api.get_version(analysisservice1)
    0

Calling `processForm` bumps the version::

    >>> analysisservice1.processForm()
    >>> api.get_version(analysisservice1)
    1


Getting a Browser View
----------------------

Getting a browser view is a common task in Bika LIMS::

    >>> api.get_view("plone")
    <Products.Five.metaclass.Plone object at 0x...>

    >>> api.get_view("workflow_action")
    <Products.Five.metaclass.WorkflowAction object at 0x...>


Getting the Request
-------------------

This function will return the global request object::

    >>> api.get_request()
    <HTTPRequest, URL=http://nohost>


Getting a Group
---------------

Users in Bika LIMS are managed in groups. A common group is the `Clients` group,
where all users of client contacts are grouped.
This function gives easy access and is also idempotent::

    >>> clients_group = api.get_group("Clients")
    >>> clients_group
    <GroupData at /plone/portal_groupdata/Clients used for /plone/acl_users/source_groups>

    >>> api.get_group(clients_group)
    <GroupData at /plone/portal_groupdata/Clients used for /plone/acl_users/source_groups>

Non-existing groups are not found::

    >>> api.get_group("NonExistingGroup")


Getting a User
--------------

Users can be fetched by their user id. The function is idempotent and handles
user objects as well::

    >>> from plone.app.testing import TEST_USER_ID
    >>> user = api.get_user(TEST_USER_ID)
    >>> user
    <MemberData at /plone/portal_memberdata/test_user_1_ used for /plone/acl_users>

    >>> api.get_user(api.get_user(TEST_USER_ID))
    <MemberData at /plone/portal_memberdata/test_user_1_ used for /plone/acl_users>

Non-existing users are not found::

    >>> api.get_user("NonExistingUser")


Getting User Properties
-----------------------

User properties, like the email or full name, are stored as user properties.
This means that they are not on the user object. This function retrieves these
properties for you::

    >>> properties = api.get_user_properties(TEST_USER_ID)
    >>> sorted(properties.items())
    [('description', ''), ('email', ''), ('error_log_update', 0.0), ('ext_editor', False), ...]

    >>> sorted(api.get_user_properties(user).items())
    [('description', ''), ('email', ''), ('error_log_update', 0.0), ('ext_editor', False), ...]

An empty property dict is returned if no user could be found::

    >>> api.get_user_properties("NonExistingUser")
    {}

    >>> api.get_user_properties(None)
    {}


Getting Users by their Roles
----------------------------

    >>> from operator import methodcaller

Roles in Bika LIMS are basically a name for one or more permissions. For
example, a `LabManager` describes a role which is granted the most permissions.

To see which users are granted a certain role, you can use this function::

    >>> labmanagers = api.get_users_by_roles(["LabManager"])
    >>> sorted(labmanagers, key=methodcaller('getId'))
    [<PloneUser 'test_labmanager'>, <PloneUser 'test_labmanager1'>, <PloneUser 'test-user'>]

A single value can also be passed into this function::

    >>> sorted(api.get_users_by_roles("LabManager"), key=methodcaller('getId'))
    [<PloneUser 'test_labmanager'>, <PloneUser 'test_labmanager1'>, <PloneUser 'test-user'>]


Getting the Current User
------------------------

Getting the current logged in user::

    >>> api.get_current_user()
    <MemberData at /plone/portal_memberdata/test_user_1_ used for /plone/acl_users>