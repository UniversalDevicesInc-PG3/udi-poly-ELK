
import re,os

def myfloat(value, prec=4):
    """ round and return float """
    return round(float(value), prec)
    
# Removes invalid charaters for ISY Node description
def get_valid_node_address(name):
    # Only allow utf-8 characters
    #  https://stackoverflow.com/questions/26541968/delete-every-non-utf-8-symbols-froms-string
    name = bytes(name, 'utf-8').decode('utf-8','ignore')
    # Remove <>`~!@#$%^&*(){}[]?/\;:"'` characters from name
    # make it lower case, and only 14 characters
    return re.sub(r"[<>`~!@#$%^&*(){}[\]?/\\;:\"']+", "", name.lower()[:14])

# Removes invalid charaters for ISY Node description
def get_valid_node_name(name):
    # Only allow utf-8 characters
    #  https://stackoverflow.com/questions/26541968/delete-every-non-utf-8-symbols-froms-string
    name = bytes(name, 'utf-8').decode('utf-8','ignore')
    # Remove <>`~!@#$%^&*(){}[]?/\;:"'` characters from name
    return re.sub(r"[<>`~!@#$%^&*(){}[\]?/\\;:\"']+", "", name)

def get_profile_info(logger):
    pvf = 'profile/version.txt'
    try:
        with open(pvf) as f:
            pv = f.read().replace('\n', '')
            f.close()
    except Exception as err:
        logger.error('get_profile_info: failed to read  file {0}: {1}'.format(pvf,err), exc_info=True)
        pv = 0
    return { 'version': pv }

def parse_range(range_in):
    range_out = list()
    for el in range_in.split(","):
        rng = el.split("-",1)
        if len(rng) > 1:
            #try:
            for i in range(int(rng[0]),int(rng[1])):
                range_out.append(i)
            range_out.append(int(rng[1]))
            #except:
            #    print("range failed")
        else:
            #try:
            range_out.append(int(el))
            #except:
            #    print("el not an int")
    return range_out

# 
# Pass in a list containing all the numbers in the set
# Return full_string and subset_str for editors
#
def reduce_subset(subset):
    subset_str = ""
    subset.sort()
    full_string = ",".join(map(str,subset))
    while len(subset) > 0:
        x = subset.pop(0)
        if subset_str != "":
            subset_str += ","
        subset_str += str(x)
        if len(subset) > 0 and x == subset[0] - 1:
            y = subset.pop(0)
            while len(subset) > 0 and (y == subset[0] or y == subset[0] - 1):
                y = subset.pop(0)
            subset_str += "-" + str(y)
    return { 'full_string': full_string, 'subset_string': subset_str }

def is_in_list(el,list_in):
    try:
        return list_in.index(el)
    except ValueError:
        return False

def make_file_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        # TODO: Trap this?
        os.makedirs(directory)
    return True

