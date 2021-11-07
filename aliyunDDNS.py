#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json
import sys
import urllib3
import requests
import ipaddress
import json
import time
import datetime
from typing import Final, Text

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.auth.credentials import AccessKeyCredential
from aliyunsdkcore.auth.credentials import StsTokenCredential
from aliyunsdkalidns.request.v20150109.DescribeDomainRecordsRequest import DescribeDomainRecordsRequest
from aliyunsdkalidns.request.v20150109.UpdateDomainRecordRequest import UpdateDomainRecordRequest

AF_INET:Final[int] = 2
AF_INET6:Final[int] = 10
TIME_OUT:Final[int] = 60


class AliyunDnsClient():
    def __init__(self, region, key_id, key_secret, domain, host):
        self.__region = region
        self.__key_id = key_id
        self.__key_secret = key_secret
        self.__domain = domain
        self.__host = host
        
        self.__credentials = AccessKeyCredential(self.__key_id, self.__key_secret)
        # use STS Token
        # credentials = StsTokenCredential('<your-access-key-id>', '<your-access-key-secret>', '<your-sts-token>')
        self.__client = AcsClient(region_id=region, credential=self.__credentials)

    def update_domain(self):
        print(self.__region)

    def get_dns_record_ip_address(self, family):
        request = DescribeDomainRecordsRequest()
        request.set_accept_format('json')
        request.set_DomainName(self.__domain)
        request.set_RRKeyWord(self.__host)
        if (family == AF_INET):
            request.set_Type("A")
        else:
            request.set_Type("AAAA")

        response = self.__client.do_action_with_exception(request)
        # python2:  print(response) 
        res = json.loads(response)
        ipaddress = str(res["DomainRecords"]["Record"][0]["Value"])
        recordid = str(res["DomainRecords"]["Record"][0]["RecordId"])
        ddnsr = DdnsRecord(recordid, ipaddress)
        return(ddnsr)

    def get_current_ip_address(self, family):
        url = "https://api.ipify.org?format=text" if family == AF_INET else "https://api64.ipify.org?format=text"
        try:
            res = requests.get(url)
            if (res.status_code == 200):
                # ip_addr_str = res.text
                if (family == AF_INET):
                    ip = ipaddress.IPv4Address(res.text)
                else:
                    ip = ipaddress.IPv6Address(res.text)
                print(Text(ip))
                return Text(ip)
            return None
        except Exception as e:
            print (e.with_traceback)
    
    def insert_dns_record(self):
        # implement if necessary 
        print ("insert_dns_record")

    def update_dns_record(self, family, record_id, record_value, rr):
        request = UpdateDomainRecordRequest()
        request.set_accept_format('json')
        request.set_RecordId(record_id)
        request.set_Value(record_value)
        request.set_RR(rr)
        if (family == AF_INET):
            request.set_Type("A")
        else:
            request.set_Type("AAAA")

        response = self.__client.do_action_with_exception(request)
        if (response != None):
            return ("success")
        else:
            return ("fail")

    def update_domain(self, family):
        if(family == AF_INET):
            print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " : start parsing IPv4 record")
        else:
            print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " : start parsing IPv6 record")
        ddnsrecord = self.get_dns_record_ip_address(family)
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " : getting dns record value")
        cur_ip_addr = self.get_current_ip_address(family)
        if (ddnsrecord.get_ip_address()==cur_ip_addr):
            print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " : ip same, not changing")
        else:
            status = self.update_dns_record(family, ddnsrecord.get_record_id(), ddnsrecord.get_ip_address(),self.__host)
            if (status == "success"):
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " :record successfully updated")

class DdnsRecord():
    def __init__(self, recordId, ipaddress):
        self.__record_id = recordId
        self.__ip_address = ipaddress

    def get_record_id(self):
        return self.__record_id

    def get_ip_address(self):
        return self.__ip_address

class Config():
    def __init__(self):
        self.__region_id = None
        self.__access_key_id = None
        self.__access_key_secret = None
        self.__domain_name = None
        self.__host_record = None
        self.__period = None

    def get_region_id(self):
        return(self.__region_id)
        
    def set_region_id(self, regionId):
        self.__region_id = regionId

    def get_access_key_id(self):
        return(self.__access_key_id)
        
    def set_access_key_id(self, access_key_id):
        self.__access_key_id = access_key_id

    def get_access_key_secret(self):
        return(self.__access_key_secret)
        
    def set_access_key_secret(self, access_key_secret):
        self.__access_key_secret = access_key_secret

    def get_domain_name(self):
        return(self.__domain_name)
        
    def set_domain_name(self, domain_name):
        self.__domain_name = domain_name

    def get_host_record(self):
        return(self.__host_record)
        
    def set_host_record(self, host_record):
        self.__host_record = host_record

    def get_period(self):
        return(self.__period)
        
    def set_period(self, period):
        self.__period = period


def _show_usage():
    print('''Usage: AliyunDDNS               [OPTION]
  -r, --region region_id        Region Id
  -i, --key-id key_id           Access Key Id
  -s, --key-secret key_secret   Access Key Secret
  -d, --domain domain           Domain Name
  -t, --host host               Host Record
  -h, --help                    Print this help''')
    sys.exit(1)

def _read_config(config_path):
    with open(config_path) as f:
        conf = json.load(f)
    # print("-c option")
    cf = Config()
    cf.set_region_id(conf["regionId"])
    cf.set_access_key_id(conf["accessKeyId"])
    cf.set_access_key_secret(conf["accessKeySecret"])
    cf.set_domain_name(conf["domainName"])
    cf.set_host_record(conf["hostRecord"])
    cf.set_period(conf["period"])
    return cf

if __name__ == "__main__":
    i = 1

    config = Config()

    while i < len(sys.argv):
        if sys.argv[i] == "-c" or sys.argv[i] == "--config":
            if i + 1 >= len(sys.argv):
                _show_usage()
            i += 1
            path = sys.argv[i]
            config = _read_config(path)
        if sys.argv[i] == "-r" or sys.argv[i] == "--region":
            if i + 1 >= len(sys.argv):
                _show_usage()
            i += 1
            config.set_region_id = sys.argv[i]
        if sys.argv[i] == "-i" or sys.argv[i] == "--key-id":
            if i + 1 >= len(sys.argv):
                _show_usage()
            i += 1
            config.set_access_key_id = sys.argv[i]
        if sys.argv[i] == "-s" or sys.argv[i] == "--key-secret":
            if i + 1 >= len(sys.argv):
                _show_usage()
            i += 1
            config.set_access_key_secret = sys.argv[i]
        if sys.argv[i] == "-d" or sys.argv[i] == "--domain":
            if i + 1 >= len(sys.argv):
                _show_usage()
            i += 1
            config.set_domain_name = sys.argv[i]
        if sys.argv[i] == "-t" or sys.argv[i] == "--host":
            if i + 1 >= len(sys.argv):
                _show_usage()
            i += 1
            config.set_host_record = sys.argv[i]
        if sys.argv[i] == "-h" or sys.argv[i] == "--help":
            _show_usage()
        i += 1
    if config.get_region_id() == None:
        print("RegionId不能为空")
        sys.exit(1)
    if config.get_access_key_id() == None:
        print("AccessKeyId不能为空")
        sys.exit(1)
    if config.get_access_key_secret() == None:
        print("AccessKeySecret不能为空")
        sys.exit(1)
    if config.get_domain_name() == None:
        print("DomainName不能为空")
        sys.exit(1)
    if config.get_host_record() == None:
        print("HostRecord不能为空")
        sys.exit(1)
    client = AliyunDnsClient(config.get_region_id(), config.get_access_key_id(), 
    config.get_access_key_secret(), config.get_domain_name(), config.get_host_record())
    client.update_domain(AF_INET)
# AliyunDnsClient

