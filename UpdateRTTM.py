''' 
   An example script which will add a newly created web server into RTTM (Dynect Real Time Traffic Mnagement) for a specific region, if the serivce or region does not exist yet they will be created
   The script uses the DynectDNS library and specifically imports DynectRest from it
   
   The credentials are read out of a configuration file in the same directory named credentials.cfg in the format:
   
   [Dynect]
   user : user_name
   customer : customer_name
   password: password
   
   
   The script has the following usage: "python UpdateRTTM.py zone fqdn region ip"
   
   zone - zone of the RTTM (ie: myzone.net)
   fqdn - the fully qualified domain name of the RTTM (ie: testrttm.myzone.net)
   region - the region to add the ip address to. If there is a space in the region, for example US East, replace the space with %20 (ie: US%20East)
   ip - the ip address of the server (ie: 1.2.3.4)
   
'''
import string
import sys
import ConfigParser
from DynectDNS import DynectRest

if (len(sys.argv) != 5):
	sys.exit("Incorrect Arguments. \n\nUsage: python UpdateRTTM.py zone fqdn region ip\n\n**If there is a space in region replace the space with %20") 

config = ConfigParser.ConfigParser()
try:
	config.read('credentials.cfg')
except:
	sys.exit("Error Reading Config file")

dynect = DynectRest()

# Log in
arguments = {
	'customer_name':  config.get('Dynect', 'customer', 'none'),
	'user_name':  config.get('Dynect', 'user', 'none'),  
	'password':  config.get('Dynect', 'password', 'none'),
}
response = dynect.execute('/Session/', 'POST', arguments)

if response['status'] != 'success':
	sys.exit("Incorrect credentials")

zone =  sys.argv[1]
fqdn =  sys.argv[2]
region =  sys.argv[3]
ip = sys.argv[4]

# first let's see if the service exists
response = dynect.execute('/RTTM/' + zone + "/" + fqdn, 'GET')

if response['status'] != 'success':
	region_clean = string.replace(region, '%20', ' ')
	region_input = {'region_code' : region_clean,  'pool' : [ {'address' : ip} ]}
	region_global = {'region_code' :  'global', 'pool' : [ {'address' : ip} ]} # we always set up a global pool with at least one address for failover since we default to global failover
	regions = [region_global, region_input]

	# select basic default values for the service
	mon = { 'protocol' : 'PING', 'interval' :  '1' }
	perf_mon = { 'protocol' : 'PING', 'interval' :  '10'}

	#build up the arguments
	args = { 'contact_nickname' : 'owner', 'performance_monitor' : perf_mon, 'monitor' :  mon, 'region' : regions}

	response = dynect.execute('/RTTM/' + zone + "/" + fqdn, 'POST', args)
	if response['status'] != 'success':
		print "Error creating service: " + str(response)
	
	sys.exit(0) #since we created the service and added the region and ip, we are done


# let's verify the region exists, if it doesn't, create it
response = dynect.execute('/RTTMRegion/' + zone + "/" + fqdn + "/" + region, 'GET')

if response['status'] != 'success':
	region_clean = string.replace(region, '%20', ' ')
	region_input = {'region_code' : region_clean,  'pool' : [ {'address' : ip} ]}
	response = dynect.execute('/RTTMRegion/' + zone + "/" + fqdn, 'POST', region_input)
	if response['status'] != 'success':
		print "Error creating region: " + str(response)
	

#finally, update the region
entry = {'address' : ip }
response = dynect.execute('/RTTMRegionPoolEntry/' + zone + "/" + fqdn + "/" + region, 'POST', entry)
post_reply = response['data']
if response['status'] != 'success':
	print "Error updating pool: " + str(response)

# Log out, to be polite
dynect.execute('/Session/', 'DELETE')