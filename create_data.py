import os
import csv
import sys
import json


class DSODB(object):
    def __init__(self):
        self._db = dict()
    def append(self,v):
        t = v['t']
        if t not in self._db:
            self._db[t] = []
        self._db[t].append(v)
    @property
    def json(self):
        index=dict()
        result = []
        for n in self._db:
            self._db[n].sort(key=lambda v:v['AM'])
            if n not in ['Ca','S']:
                result += self._db[n]
                index[n]=len(result)
        result += self._db['Ca']
        index['Ca']=len(result)
        result += self._db['S']
        index['S']=len(result)
        return result,index



def parse_ra(val):
    h,m,s = val.split(':')
    return 15*(int(h)  + (60*int(m) + float(s))/3600)

def parse_de(val):
    d,m,s = val.split(':')
    deg = int(d)
    sign = 1 if deg >= 0 else -1
    return sign*(abs(deg)  + (60*int(m) + float(s))/3600)

def get_OpenNGC_DSO(result):
    # M45 is missing
    result.append(dict(DE=24.11666,RA=56.75,name='M45',t='Oc',AM=1.6))
    with open('OpenNGC/NGC.csv','r') as f:
        mapped = set(range(1,111));
        ngc_mapping = {
            '*': None,
            '**': None,
            '*Ass': 'Oc',
            'OCl': 'Oc',
            'GCl': 'Gc',
            'Cl+N': 'Ne',
            'G': 'Ga',
            'GPair': 'Ga',
            'GTrpl': 'Ga',
            'GGroup': 'Ga',
            'PN': 'Ne',
            'HII': 'Ne',
            'DrkN': 'Ne',
            'EmN': 'Ne',
            'Neb': 'Ne',
            'RfN': 'Ne',
            'SNR': 'Ne',
            'Nova': None,
            'NonEx': None,
            'Dup': None,
            'Other': None
        }
        for i,row in enumerate(csv.reader(f,delimiter=';')):
            if i<=1:
                continue
            object_id = row[0]
            object_type = row[1]
            object_type = ngc_mapping.get(object_type)
            if object_type is None:
                continue
            ra = parse_ra(row[2])
            de = parse_de(row[3])
            if row[9] == '':
                continue
            mag = float(row[9])
            messier = int(row[18]) if row[18]!='' else 0
            #hack data
            if object_id == 'NGC5866':
                messier = 102
            if messier:
                mapped.remove(messier)
                object_id = 'M%d' % messier
            result.append(dict(RA=ra,DE=de,AM=mag,name=object_id,t=object_type))
    return result

def get_stars(allstars):
    starpos = dict()
    with open('western_constellations_atlas_of_space' + '/data/hygdata_v3/hygdata_v3.csv','r') as f:
        for i,row in enumerate(csv.reader(f)):
            if i <= 1:
                continue
            sid = row[1]
            name=row[6]
            if name == '':
                name = None
            ra=float(row[7])*15.0
            de=float(row[8])
            if sid!='':
                starpos[int(sid)] = (ra,de,name)
            mag=float(row[13])
            if mag <= 6.5:
               objects.append(dict(DE=de,RA=ra,AM=mag,name=name,t='S'))

    return starpos

def get_atlas_DSO(messier):
    with open('western_constellations_atlas_of_space' + '/data/processed/messier_ngc_processed.csv','r') as f:
        for i,row in enumerate(csv.reader(f)):
            if i <= 0:
                continue
            name=row[0]
            t=row[1]
            ra=float(row[2])*15.0
            de=float(row[3])
            mag=float(row[4])
            if t.find('nebula')!=-1:
                t='Ne'
            elif t.find('open clu')!=-1:
                t='Oc'
            elif t.find('galaxy')!=-1:
                t='Ga'
            elif t.find('globular')!=-1:
                t='Gc'
            elif t.find('clou')!=-1:
                t='Oc'
            else:
                print("Skipping",t,name);
                continue
            messier.append(dict(DE=de,RA=ra,AM=mag,name=name,t=t))
    return messier

def get_constellations(cons):
    os.system('iconv -f latin1 -t utf-8 ' + 'western_constellations_atlas_of_space' + '/data/processed/centered_constellations.csv -o /tmp/ct_utf8.csv')
    with open('/tmp/ct_utf8.csv','r') as f:
        for i,row in enumerate(csv.reader(f)):
            if i <= 0:
                continue
            name=row[0]
            t=row[1]
            ra=float(row[4])*15.0
            de=float(row[5])
            cons.append(dict(DE=de,RA=ra,AM=-1,name=name,t='Ca'))
    return cons;

def get_constellation_lines(starpos):
    lines=[]
    with open('western_constellations_atlas_of_space' + '/data/stellarium_western_asterisms/constellationship.fab','r') as f:
        for line in f.readlines():
            row=line.split(' ')
            row=filter(lambda v:v!='',row)
            N=int(row[1])
            pairs = [int(v) for v in row[2:]]
            for k in range(N):
                p0 = pairs[k*2]
                p1 = pairs[k*2+1]
                line=dict(r0=starpos[p0][0],
                          d0=starpos[p0][1],
                          r1=starpos[p1][0],
                          d1=starpos[p1][1])
                lines.append(line)
    return lines

def make_jsbd(dso,lines):
    with open('jsdb.js','w') as f:
        f.write("//Generated from https://github.com/eleanorlutz/western_constellations_atlas_of_space\n")
        f.write("// Lincense: https://github.com/eleanorlutz/western_constellations_atlas_of_space/blob/main/LICENSE (GPL)\n")
        f.write("// DSO data from https://github.com/mattiaverga/OpenNGC by CC-BY-SA-v4.0\n")
        f.write("// types: 'S' - star,'Ca' - canstelation,  'Oc' - open cluster, 'Gc' = globular cluster, 'Ga' - gallaxy, 'Ne' - nebula\n")
        db,index=dso.json
        f.write('var allstars_index = ' + json.dumps(index) +';\n');
        f.write('var allstars = ')
        json.dump(db,f,indent=2)
        f.write(';\n')
        f.write('var constellation_lines = ')
        json.dump(lines,f,indent=2)
        f.write(';\n')

if __name__ == "__main__":
    objects = DSODB()
    #get_atlas_DSO(objects)
    get_OpenNGC_DSO(objects)
    mapping = get_stars(objects);
    get_constellations(objects);
    lines = get_constellation_lines(mapping)
    make_jsbd(objects,lines)


