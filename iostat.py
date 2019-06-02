#!/usr/bin/python
import sys
import time
import re

pattern = re.compile('[0-9]+')

i_dev_name=2
i_rd_ios=3
i_rd_merges=4
i_rd_sectors=5
i_rd_ticks=6
i_wr_ios=7
i_wr_merges=8
i_wr_sectors=9
i_wr_ticks=10
i_in_flight=11
i_io_ticks=12
i_time_in_queue=13

def digitization(dev_stats):
    for dev_info in dev_stats.values():
        for i in range(3, len(dev_info)):
            dev_info[i]=long(dev_info[i])

def read_diskstats(dev):
    ret={}
    with open('/proc/diskstats', 'r') as f:
        diskstats=f.readlines()
    
    for ds in diskstats:
        dev_info=ds.split()
        if dev != None:
            if dev_info[i_dev_name] == dev:
                ret[dev_info[i_dev_name]]=dev_info
                break
        elif not re.search(pattern, dev_info[i_dev_name]):
                ret[dev_info[i_dev_name]]=dev_info
    digitization(ret)
    return ret

it_dev_name=0
it_rrqm=1
it_wrqm=2
it_r=3
it_w=4
it_rsec=5
it_wsec=6
it_ravgrq_sz=7
it_wavgrq_sz=8
it_avgrq_sz=9
it_avgqu_sz=10
it_rawait=11
it_wawait=12
it_await=13
it_util=14

headers_fmt=['%-8s', '%8s', '%8s', '%8s', '%8s', '%8s', '%8s', '%11s', '%11s', '%10s', '%10s', '%8s', '%8s', '%8s', '%8s']
headers=['Device:', 'rrqm/s', 'wrqm/s', 'r/s', 'w/s', 'rsec/s', 'wsec/s', 'ravgrq-sz', 'wavgrq-sz', 'avgrq-sz', 'avgqu-sz', 'r_await', 'w_await', 'await', '%util']
items_fmt=['%-8s', '%8.2f', '%8.2f', '%8.2f', '%8.2f', '%8.2f', '%8.2f', '%11.2f', '%11.2f', '%10.2f', '%10.2f', '%8.2f', '%8.2f', '%8.2f', '%8.2f']

dsp_fmt={
'b': [it_dev_name,it_rrqm,it_wrqm,it_r,it_w,it_rsec,it_wsec,it_avgrq_sz,it_avgqu_sz,it_await,it_util],
'x': [it_dev_name,it_rrqm,it_wrqm,it_r,it_w,it_rsec,it_wsec,it_avgrq_sz,it_avgqu_sz,it_await,it_rawait,it_wawait,it_util],
'X': [it_dev_name,it_rrqm,it_wrqm,it_r,it_w,it_rsec,it_wsec,it_avgrq_sz,it_ravgrq_sz,it_wavgrq_sz,it_avgqu_sz,it_await,it_rawait,it_wawait,it_util]
}

unit_info={
'm': ['MB', 2048.0],
'k': ['KB', 2.0],
's': ['sec', 1.0]
}

def display(iostats, dsp_mode, unit):
    fmt=dsp_fmt[dsp_mode]
    ui=unit_info[unit]
    
    headers[it_rsec]='r'+ui[0]+'/s'
    headers[it_wsec]='w'+ui[0]+'/s'
    
    hdr_fmt=''
    hdr=[]
    itm_fmt=''
    
    for i in fmt:
        hdr_fmt+=headers_fmt[i]+' '
        hdr.append(headers[i])
        itm_fmt+=items_fmt[i]+' '
    
    print hdr_fmt % tuple(hdr)
    
    for iostat in iostats:
        itm=[]
        for i in fmt:
            itm.append(iostat[i] if i != it_rsec and i != it_wsec else iostat[i]/ui[1])
        print itm_fmt % tuple(itm)
    
    print ''

def calc_items(new_stats, old_stats, itv):
    ret=[]

    for new in new_stats.values():
        if new[i_dev_name] not in old_stats.keys():
            old_stats[new[i_dev_name]]=[0,0,new[i_dev_name],0,0,0,0,0,0,0,0,0,0,0]
        old = old_stats[new[i_dev_name]]
        
        nr_rd_ios=new[i_rd_ios]-old[i_rd_ios]
        nr_wr_ios=new[i_wr_ios]-old[i_wr_ios]
        nr_ios=nr_rd_ios+nr_wr_ios
        
        nr_rd_secs=new[i_rd_sectors]-old[i_rd_sectors]
        nr_wr_secs=new[i_wr_sectors]-old[i_wr_sectors]
        nr_secs=nr_rd_secs+nr_wr_secs
        
        nr_rd_ticks=new[i_rd_ticks]-old[i_rd_ticks]
        nr_wr_ticks=new[i_wr_ticks]-old[i_wr_ticks]
        nr_ticks=nr_rd_ticks+nr_wr_ticks
        
        iostat=[]
        iostat.append(new[i_dev_name])                                          #dev_name
        iostat.append((new[i_rd_merges]-old[i_rd_merges])/itv)                  #rrqm/s
        iostat.append((new[i_wr_merges]-old[i_wr_merges])/itv)                  #wrqm/s
        iostat.append(nr_rd_ios/itv)                                            #r/s
        iostat.append(nr_wr_ios/itv)                                            #w/s
        iostat.append(nr_rd_secs/itv)                                           #rsec/s
        iostat.append(nr_wr_secs/itv)                                           #wsec/s
        iostat.append(nr_rd_secs/float(nr_rd_ios) if nr_rd_ios != 0 else 0.0)   #ravgrq-sz
        iostat.append(nr_wr_secs/float(nr_wr_ios) if nr_wr_ios != 0 else 0.0)   #wavgrq-sz
        iostat.append(nr_secs/float(nr_ios) if nr_ios != 0 else 0.0)            #avgrq-sz
        iostat.append((new[i_time_in_queue]-old[i_time_in_queue])/(itv*1000.0)) #avgqu-sz
        iostat.append(nr_rd_ticks/float(nr_rd_ios) if nr_rd_ios != 0 else 0.0)  #r_await
        iostat.append(nr_wr_ticks/float(nr_wr_ios) if nr_wr_ios != 0 else 0.0)  #w_await
        iostat.append(nr_ticks/float(nr_ios) if nr_ios != 0 else 0.0)           #await
        iostat.append((new[i_io_ticks]-old[i_io_ticks])/(itv*10.0))             #%util
        
        ret.append(iostat)
    return ret

new_stats={}
old_stats={}

def io_stat(params):
    global new_stats
    global old_stats

    new_stats=read_diskstats(params['dev'])
    iostats=calc_items(new_stats, old_stats, float(params['itv']))
    display(iostats, params['dsp_mode'], params['unit'])
    old_stats=new_stats

def parse_param(params):
    if len(sys.argv) == 2 and (sys.argv[1] == '-h' or sys.argv[1] == '--help'):
        params['err']=1
        return

    for arg in sys.argv[1:]:
        if arg.isdigit(): params['itv']=int(arg)
        elif arg.isalpha(): params['dev']=arg
        elif arg[0]=='-' and arg[1:].isalpha():
            for opt in arg[1:]:
                if opt in 'bxX': params['dsp_mode']=opt
                elif opt in 'mks': params['unit']=opt
                else:
                    print 'unknown option: '+opt
                    params['err']=1
                    return
        else:
            print 'unknown arg: '+arg
            params['err']=1
            return

def print_usage():
    print 'Usage: %s [option] [interval] [device]' % sys.argv[0]
    print 'Optioins:'
    print '        display_mode: [-b*] [-x] [-X]'
    print '        unit: [-m*] [-k] [-s]'

def main():
    params={'itv':1, 'dev':None, 'dsp_mode':'b', 'unit':'m'}
    parse_param(params)
    if 'err' in params:
        print_usage()
        return
    
    while(True):
        io_stat(params)
        time.sleep(params['itv'])

main()