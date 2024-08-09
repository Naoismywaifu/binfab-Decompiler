import struct

def decode_var_length_int(data):
    value = 0
    shift = 0
    length = 0
    for byte in data:
        value |= (byte & 0x7F) << shift
        length += 1
        if byte & 0x80 == 0:
            break
        shift += 7
    return value, length

def decode_signed_int(value):
    if value & 1:
        return -(value >> 1)
    else:
        return value >> 1

def read_prefab_integer(data, index):
    value, length = decode_var_length_int(data[index:])
    signed_value = decode_signed_int(value)
    return signed_value, length

def read_float(data, index):
    return struct.unpack('f', data[index:index+4])[0], 4

def read_double(data, index):
    return struct.unpack('d', data[index:index+8])[0], 8

def read_string(data, index):
    length, length_size = decode_var_length_int(data[index:])
    string_data = data[index + length_size: index + length_size + length]
    try:
        string_value = string_data.decode('utf-8')
    except UnicodeDecodeError as e:
        print(f"Error decoding string at index {index}: {e}")
        string_value = string_data.decode('utf-8', errors='replace')
    return string_value, length_size + length

def decode_object_array(data, index=0):
    decoded_data = []
    while index < len(data):
        value, value_length = read_prefab_integer(data, index)
        data_type = value & 0x07
        actual_value = value >> 3
        index += value_length
        if data_type == 0:  # signed integer
            decoded_data.append(actual_value)
        elif data_type == 1:  # unsigned integer
            decoded_data.append(actual_value)
        elif data_type == 2:  # single precision float
            float_value, float_length = read_float(data, index)
            decoded_data.append(float_value)
            index += float_length
        elif data_type == 3:  # double precision float
            double_value, double_length = read_double(data, index)
            decoded_data.append(double_value)
            index += double_length
        elif data_type == 4:  # string
            string_value, string_length = read_string(data, index)
            decoded_data.append(string_value)
            index += string_length
        elif data_type == 7:  # object
            if actual_value == 1:  # end of object
                break
            elif actual_value == 2:  # array list
                sub_array, sub_length = decode_object_array(data, index)
                decoded_data.append(sub_array)
                index += sub_length
        if index < len(data) and data[index] == 0x1E:  # End of object array
            index += 1
            break
    return decoded_data, index

def extract_damage_data(object_array):
    damage_data = {}
    for index, value in enumerate(object_array):
        if index == 1:
            damage_data['fixed_base_damage'] = value
        elif index == 12:
            damage_data['base_damage_multiplier'] = value
        elif index == 25:
            damage_data['CD_multiplier'] = value
    return damage_data

def read_binfab_file(filename):
    with open(filename, 'rb') as file:
        return file.read()

def main(binfab_file):
    data = read_binfab_file(binfab_file)
    decoded_object, _ = decode_object_array(data)
    damage_data = extract_damage_data(decoded_object)
    
    print("Decoded Object:", decoded_object)
    print("Damage Data:", damage_data)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python decode_binfab.py <binfab_file>")
        sys.exit(1)
    binfab_file = sys.argv[1]
    main(binfab_file)
