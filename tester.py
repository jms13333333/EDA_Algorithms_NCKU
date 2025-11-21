#!/usr/bin/env python
import os 
from operator import itemgetter
from itertools import combinations
import sys

def read_node_file(fopen): #wtf why can you ignore all non-macro whywhywhywhywhywhywhywhywhwy?????
    
    node_info = {}
    node_info_raw_id_name ={}
    node_cnt = 0
    for line in fopen.readlines():
        if not (line.startswith("\t") or line.startswith(" ")):
            continue
        line = line.strip().split()
        if line[-1] != "terminal":
            continue
        node_name = line[0]
        x = int(line[1])
        y = int(line[2])
        node_info[node_name] = {"id": node_cnt, "x": x , "y": y }
        node_info_raw_id_name[node_cnt] = node_name
        node_cnt += 1
    print("len node_info", len(node_info))
    return node_info, node_info_raw_id_name

def read_net_file(fopen, node_info):
    net_info = {}
    net_name = None
    net_cnt = 0
    for line in fopen.readlines():
        if not (line.startswith("\t") or line.startswith(" ")) and not line.startswith("NetDegree"):
            continue
        line = line.strip().split()
        if line[0] == "NetDegree":
            net_name = line[-1]
        else:
            node_name = line[0]
            if node_name in node_info:
                if not net_name in net_info:
                    net_info[net_name] = {}
                    net_info[net_name]["nodes"] = {}
                    net_info[net_name]["ports"] = {}
                if not node_name in net_info[net_name]["nodes"]:
                    x_offset = float(line[-2])
                    y_offset = float(line[-1])
                    net_info[net_name]["nodes"][node_name] = {}
                    net_info[net_name]["nodes"][node_name] = {"x_offset": x_offset, "y_offset": y_offset}
    for net_name in list(net_info.keys()):
        if len(net_info[net_name]["nodes"]) <= 1:
            net_info.pop(net_name)
    for net_name in net_info:
        net_info[net_name]['id'] = net_cnt
        net_cnt += 1
    print("adjust net size = {}".format(len(net_info)))
    return net_info

def get_comp_hpwl_dict(node_info, net_info):
    comp_hpwl_dict = {}
    for net_name in net_info:
        max_idx = 0
        for node_name in net_info[net_name]["nodes"]:
            max_idx = max(max_idx, node_info[node_name]["id"])
        if not max_idx in comp_hpwl_dict:
            comp_hpwl_dict[max_idx] = []
        comp_hpwl_dict[max_idx].append(net_name)
    return comp_hpwl_dict

def get_node_to_net_dict(node_info, net_info):
    node_to_net_dict = {}
    for node_name in node_info:
        node_to_net_dict[node_name] = set()
    for net_name in net_info:
        for node_name in net_info[net_name]["nodes"]:
            node_to_net_dict[node_name].add(net_name)
    return node_to_net_dict

def get_port_to_net_dict(port_info, net_info):
    port_to_net_dict = {}
    for port_name in port_info:
        port_to_net_dict[port_name] = set()
    for net_name in net_info:
        for port_name in net_info[net_name]["ports"]:
            port_to_net_dict[port_name].add(net_name)
    return port_to_net_dict

def read_pl_file(fopen, node_info):
    for line in fopen.readlines():
        if not line.startswith('o'):
            continue
        line = line.strip().split()
        node_name = line[0]
        if not node_name in node_info:
            continue
        if len(line) == 6:
            if line[5] == '/FIXED':
                node_info[node_name]['movable'] = False # Fixed / False
        else:
            node_info[node_name]['movable'] = True # Movable
        rotation = line[4]
        place_x = int(line[1])
        place_y = int(line[2])
        node_info[node_name]['x_pos_raw'] = place_x
        node_info[node_name]['y_pos_raw'] = place_y
        node_info[node_name]['rotation_raw'] = rotation
    return True

def read_pl_out_file(fopen, node_info): #return True, preplaced information remained
    for line in fopen.readlines():
        if not line.startswith('o'):
            continue
        line = line.strip().split()
        node_name = line[0]
        if not node_name in node_info:
            print(f'好像有不是macro的東西混進來了OAO')
            continue
        rotation = line[4]
        place_x = int(line[1])
        place_y = int(line[2])
        if node_info[node_name]['movable'] == False: # preplaced
            ###  check if the information of the preplaced macro is changed ###
            if (rotation != node_info[node_name]['rotation_raw'] or place_x != node_info[node_name]['x_pos_raw'] or place_y != node_info[node_name]['y_pos_raw']):
                print('動到preplaced macro了!')
                return False
            node_info[node_name]['rotation'] = rotation
            node_info[node_name]['x_pos'] = place_x
            node_info[node_name]['y_pos'] = place_y
        else:
            node_info[node_name]['rotation'] = rotation
            node_info[node_name]['x_pos'] = place_x
            node_info[node_name]['y_pos'] = place_y
    return True

            
        



def get_node_id_to_name(node_info, node_to_net_dict):
    node_name_and_num = []
    for node_name in node_info:
        node_name_and_num.append((node_name, len(node_to_net_dict[node_name])))
    node_name_and_num = sorted(node_name_and_num, key=itemgetter(1), reverse = True)
    print("node_name_and_num", node_name_and_num)
    node_id_to_name = [node_name for node_name, _ in node_name_and_num]
    for i, node_name in enumerate(node_id_to_name):
        node_info[node_name]["id"] = i
    return node_id_to_name

def get_node_id_to_name_topology(node_info, node_to_net_dict, net_info, benchmark):
    node_id_to_name = []
    adjacency = {}
    for net_name in net_info:
        for node_name_1, node_name_2 in list(combinations(net_info[net_name]['nodes'],2)):
            if node_name_1 not in adjacency:
                adjacency[node_name_1] = set()
            if node_name_2 not in adjacency:
                adjacency[node_name_2] = set()
            adjacency[node_name_1].add(node_name_2)
            adjacency[node_name_2].add(node_name_1)

    visited_node = set()

    node_net_num = {}
    for node_name in node_info:
        node_net_num[node_name] = len(node_to_net_dict[node_name])
    
    node_net_num_fea= {}
    node_net_num_max = max(node_net_num.values())
    print("node_net_num_max", node_net_num_max)
    for node_name in node_info:
        node_net_num_fea[node_name] = node_net_num[node_name]/node_net_num_max
    
    node_area_fea = {}
    node_area_max_node = max(node_info, key = lambda x : node_info[x]['x'] * node_info[x]['y'])
    node_area_max = node_info[node_area_max_node]['x'] * node_info[node_area_max_node]['y']
    print("node_area_max = {}".format(node_area_max))
    for node_name in node_info:
        node_area_fea[node_name] = node_info[node_name]['x'] * node_info[node_name]['y'] / node_area_max
    
    if "V" in node_info:
        add_node = "V"
        visited_node.add(add_node)
        node_id_to_name.append((add_node, node_net_num[add_node]))
        node_net_num.pop(add_node)
    
    add_node = max(node_net_num, key = lambda v: node_net_num[v])
    visited_node.add(add_node)
    node_id_to_name.append((add_node, node_net_num[add_node]))
    node_net_num.pop(add_node)

    while len(node_id_to_name) < len(node_info):
        candidates = {}
        for node_name in visited_node:
            if node_name not in adjacency:
                continue
            for node_name_2 in adjacency[node_name]:
                if node_name_2 in visited_node:
                    continue
                if node_name_2 not in candidates:
                    candidates[node_name_2] = 0
                candidates[node_name_2] += 1
        for node_name in node_info:
            if node_name not in candidates and node_name not in visited_node:
                candidates[node_name] = 0
        if len(candidates) > 0:
            if benchmark != 'ariane':
                if benchmark == "bigblue3":
                    add_node = max(candidates, key = lambda v: candidates[v]*1 + node_net_num[v]*100000 +\
                        node_info[v]['x']*node_info[v]['y'] * 1 +int(hash(v)%10000)*1e-6)
                else:
                    add_node = max(candidates, key = lambda v: candidates[v]*1 + node_net_num[v]*1000 +\
                        node_info[v]['x']*node_info[v]['y'] * 1 +int(hash(v)%10000)*1e-6)
            else:
                add_node = max(candidates, key = lambda v: candidates[v]*30000 + node_net_num[v]*1000 +\
                    node_info[v]['x']*node_info[v]['y']*1 +int(hash(v)%10000)*1e-6)
        else:
            if benchmark != 'ariane':
                if benchmark == "bigblue3":
                    add_node = max(node_net_num, key = lambda v: node_net_num[v]*100000 + node_info[v]['x']*node_info[v]['y']*1)
                else:
                    add_node = max(node_net_num, key = lambda v: node_net_num[v]*1000 + node_info[v]['x']*node_info[v]['y']*1)
            else:
                add_node = max(node_net_num, key = lambda v: node_net_num[v]*1000 + node_info[v]['x']*node_info[v]['y']*1)

        visited_node.add(add_node)
        node_id_to_name.append((add_node, node_net_num[add_node])) 
        node_net_num.pop(add_node)
    for i, (node_name, _) in enumerate(node_id_to_name):
        node_info[node_name]["id"] = i
    # print("node_id_to_name")
    # print(node_id_to_name)
    node_id_to_name_res = [x for x, _ in node_id_to_name]
    return node_id_to_name_res

class PlaceDB_adaptec():

    def __init__(self, benchmark = "adaptec1"):
        self.benchmark = benchmark
        if benchmark == "ariane" or benchmark == "sample_clustered":
            path = benchmark + '/netlist.pb.txt'
            pbtxt = get_netlist_info_dict(path)
            self.node_info, self.node_info_raw_id_name = get_node_info(pbtxt)
            self.node_cnt = len(self.node_info)
            self.net_info, self.port_info = get_net_info(pbtxt)
            self.net_cnt = len(self.net_info)
            self.max_height, self.max_width = 357, 357
            self.port_to_net_dict = get_port_to_net_dict(self.port_info, self.net_info)
        else:
            #assert os.path.exists(benchmark)
            node_file = open(os.path.join( benchmark+".nodes"), "r") 
            self.node_info, self.node_info_raw_id_name = read_node_file(node_file)  #read_node_file
            pl_file = open(os.path.join(benchmark+".pl"), "r")
            self.port_info = {}
            self.node_cnt = len(self.node_info)
            node_file.close()
            net_file = open(os.path.join(benchmark+".nets"), "r")
            self.net_info = read_net_file(net_file, self.node_info) #read_net_file
            self.net_cnt = len(self.net_info)
            net_file.close()
            pl_file = open(os.path.join(benchmark+".pl"), "r")
            read_pl_file(pl_file, self.node_info) #read_pl_file
            #print("max_width = {}".format(self.max_width))
            #print("max_height = {}".format(self.max_height))
            pl_file.close()
            pl_out_file = open(os.path.join(benchmark+".pl_out"), "r")
            preplaced_retained = read_pl_out_file(pl_out_file, self.node_info)
            if preplaced_retained == False:
                sys.exit()
            pl_out_file.close()
            self.port_to_net_dict = {}
        self.node_to_net_dict = get_node_to_net_dict(self.node_info, self.net_info)
        self.node_id_to_name = get_node_id_to_name_topology(self.node_info, self.node_to_net_dict, self.net_info, self.benchmark)

    def debug_str(self):
        print("node_cnt = {}".format(len(self.node_info)))
        print("net_cnt = {}".format(len(self.net_info)))
        print("max_height = {}".format(self.max_height))
        print("max_width = {}".format(self.max_width))

def check_overlap(node_info):
    for n in node_info:
        x_l, y_l = node_info[n]['x_pos'], node_info[n]['y_pos']
        if (node_info[n]['rotation'] == 'N' or node_info[n]['rotation'] == 'FS' or node_info[n]['rotation'] == 'FN' or node_info[n]['rotation'] == 'S'):
            size_x, size_y = node_info[n]['x'], node_info[n]['y']
        elif (node_info[n]['rotation'] == 'W' or node_info[n]['rotation'] == 'E' or node_info[n]['rotation'] == 'FW' or node_info[n]['rotation'] == 'FE'):
            size_x, size_y = node_info[n]['y'], node_info[n]['x']
        else:
            print(f'轉向錯誤 (不包含八種轉向之一): {n}')
            sys.exit()
        x_r = x_l + size_x
        y_r = y_l + size_y
        for n_ in node_info:
            if n == n_:
                continue
            x_l_, y_l_ = node_info[n_]['x_pos'], node_info[n_]['y_pos']
            if (node_info[n_]['rotation'] == 'N' or node_info[n_]['rotation'] == 'FS' or node_info[n_]['rotation'] == 'FN' or node_info[n_]['rotation'] == 'S'):
                size_x_, size_y_ = node_info[n_]['x'], node_info[n_]['y']
            elif (node_info[n_]['rotation'] == 'W' or node_info[n_]['rotation'] == 'E' or node_info[n_]['rotation'] == 'FW' or node_info[n_]['rotation'] == 'FE'):
                size_x_, size_y_ = node_info[n_]['y'], node_info[n_]['x']
            else:
                print(f'轉向錯誤 (不包含八種轉向之一): {n_}')
                sys.exit()
            x_r_ = x_l_ + size_x_
            y_r_ = y_l_ + size_y_
            if not (x_l >= x_r_ or x_r <= x_l_ or y_l >= y_r_ or y_r <= y_l_):
                print(f'存在overlap!!: {n} 與 {n_}')
                return True # True 有重疊
    return False

def cal_HPWL(placedb):
    hpwl = 0.0
    for net_name in placedb.net_info:
        max_x = 0.0
        min_x = 99999999999
        max_y = 0.0
        min_y = 99999999999
        for node_name in placedb.net_info[net_name]["nodes"]:
            if node_name not in placedb.node_info:
                continue
            rotation = placedb.node_info[node_name]['rotation']
            if rotation == 'N':
                h = placedb.node_info[node_name]['x']
                w = placedb.node_info[node_name]['y']
                pin_x = placedb.node_info[node_name]['x_pos'] + h / 2.0 + placedb.net_info[net_name]["nodes"][node_name]["x_offset"]  #最左下+一半長寬+offset從中間算
                pin_y = placedb.node_info[node_name]['y_pos'] + w / 2.0 + placedb.net_info[net_name]["nodes"][node_name]["y_offset"]
            elif rotation == 'S':
                h = placedb.node_info[node_name]['x']
                w = placedb.node_info[node_name]['y']
                pin_x = placedb.node_info[node_name]['x_pos'] + h / 2.0 - placedb.net_info[net_name]["nodes"][node_name]["x_offset"]  #最左下+一半長寬+offset從中間算
                pin_y = placedb.node_info[node_name]['y_pos'] + w / 2.0 - placedb.net_info[net_name]["nodes"][node_name]["y_offset"]
            elif rotation == 'W':
                h = placedb.node_info[node_name]['y']
                w = placedb.node_info[node_name]['x']
                pin_x = placedb.node_info[node_name]['x_pos'] + h / 2.0 - placedb.net_info[net_name]["nodes"][node_name]["y_offset"]  #最左下+一半長寬+offset從中間算
                pin_y = placedb.node_info[node_name]['y_pos'] + w / 2.0 + placedb.net_info[net_name]["nodes"][node_name]["x_offset"]
            elif rotation == 'E':
                h = placedb.node_info[node_name]['y']
                w = placedb.node_info[node_name]['x']
                pin_x = placedb.node_info[node_name]['x_pos'] + h / 2.0 + placedb.net_info[net_name]["nodes"][node_name]["y_offset"]  #最左下+一半長寬+offset從中間算
                pin_y = placedb.node_info[node_name]['y_pos'] + w / 2.0 - placedb.net_info[net_name]["nodes"][node_name]["x_offset"]
            elif rotation == 'FN':
                h = placedb.node_info[node_name]['x']
                w = placedb.node_info[node_name]['y']
                pin_x = placedb.node_info[node_name]['x_pos'] + h / 2.0 - placedb.net_info[net_name]["nodes"][node_name]["x_offset"]  #最左下+一半長寬+offset從中間算
                pin_y = placedb.node_info[node_name]['y_pos'] + w / 2.0 + placedb.net_info[net_name]["nodes"][node_name]["y_offset"]
            elif rotation == 'FS':
                h = placedb.node_info[node_name]['x']
                w = placedb.node_info[node_name]['y']
                pin_x = placedb.node_info[node_name]['x_pos'] + h / 2.0 + placedb.net_info[net_name]["nodes"][node_name]["x_offset"]  #最左下+一半長寬+offset從中間算
                pin_y = placedb.node_info[node_name]['y_pos'] + w / 2.0 - placedb.net_info[net_name]["nodes"][node_name]["y_offset"]
            elif rotation == 'FW':
                h = placedb.node_info[node_name]['y']
                w = placedb.node_info[node_name]['x']
                pin_x = placedb.node_info[node_name]['x_pos'] + h / 2.0 + placedb.net_info[net_name]["nodes"][node_name]["y_offset"]  #最左下+一半長寬+offset從中間算
                pin_y = placedb.node_info[node_name]['y_pos'] + w / 2.0 + placedb.net_info[net_name]["nodes"][node_name]["x_offset"]
            elif rotation == 'FE':
                h = placedb.node_info[node_name]['y']
                w = placedb.node_info[node_name]['x']
                pin_x = placedb.node_info[node_name]['x_pos'] + h / 2.0 - placedb.net_info[net_name]["nodes"][node_name]["y_offset"]  #最左下+一半長寬+offset從中間算
                pin_y = placedb.node_info[node_name]['y_pos'] + w / 2.0 - placedb.net_info[net_name]["nodes"][node_name]["x_offset"]
            max_x = max(pin_x, max_x)
            min_x = min(pin_x, min_x)
            max_y = max(pin_y, max_y)
            min_y = min(pin_y, min_y)
        for port_name in placedb.net_info[net_name]["ports"]:
            h = placedb.port_info[port_name]['x']
            w = placedb.port_info[port_name]['y']
            pin_x = h
            pin_y = w
            max_x = max(pin_x, max_x)
            min_x = min(pin_x, min_x)
            max_y = max(pin_y, max_y)
            min_y = min(pin_y, min_y)
        hpwl_tmp = (max_x - min_x) + (max_y - min_y)
        hpwl += hpwl_tmp
    return hpwl

if __name__ == "__main__":
    folder = 'benchmarks/'
    if sys.argv[1] == '--case':
        name = sys.argv[2]
    file = folder + name + '/' + name
    PlaceDB =PlaceDB_adaptec(file)
    if check_overlap(PlaceDB.node_info) == True:
        sys.exit()
    print(f'Macro HPWL: {cal_HPWL(PlaceDB)}')
    




