#   igc2kmz EXIF functions
#   Copyright (C) 2008  Tom Payne
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import struct


BIG_ENDIAN, = struct.unpack('=H', 'MM')
LITTLE_ENDIAN, = struct.unpack('=H', 'II')
BYTE_ORDER_CHAR = {BIG_ENDIAN: '>', LITTLE_ENDIAN: '<'}

BYTE = 1
ASCII = 2
SHORT = 3
LONG = 4
RATIONAL = 5
UNDEFINED = 7
SLONG = 9
SRATIONAL = 10
DATA_TYPE_LENGTH = {
        BYTE: 1,
        ASCII: 1,
        SHORT: 2,
        LONG: 4,
        RATIONAL: 8,
        UNDEFINED: 1,
        SLONG: 4,
        SRATIONAL: 8}
DATA_TYPE_FORMAT = {
        BYTE: 'B',
        ASCII: 'c',
        SHORT: 'H',
        LONG: 'L',
        RATIONAL: 'L',
        UNDEFINED: 'B',
        SLONG: 'l',
        SRATIONAL: 'l'}


class SyntaxError(RuntimeError):
    pass


class TIFF(object):

    def __init__(self, data):
        self.data = data
        self.byte_order, = struct.unpack('=H', self.data[0:2])
        if not self.byte_order in BYTE_ORDER_CHAR:
            raise SyntaxError, 'Unsupported byte order %s' \
                               % repr(self.data[6:8])
        self.byte_order_char = BYTE_ORDER_CHAR[self.byte_order]
        self.version, self.first_ifd_offset = \
            struct.unpack(self.byte_order_char + 'HL', self.data[2:8])
        if self.version != 42:
            raise SyntaxError, 'Unsupported version %s' % self.version

    def ifd_tags(self, offset):
        n, = struct.unpack(self.byte_order_char + 'H',
                           self.data[offset:offset + 2])
        for i in xrange(0, n):
            sl = slice(offset + 2 + 12 * i, offset + 2 + 12 * i + 8)
            tag, data_type, count = struct.unpack(self.byte_order_char + 'HHL',
                                                  self.data[sl])
            if not data_type in DATA_TYPE_LENGTH:
                raise SyntaxError, 'Unrecognised data type %d' % data_type
            data_length = DATA_TYPE_LENGTH[data_type] * count
            if data_length > 4:
                sl = slice(offset + 2 + 12 * i + 8, offset + 2 + 12 * i + 12)
                data_offset, = struct.unpack(self.byte_order_char + 'L',
                                             self.data[sl])
                data_slice = slice(data_offset, data_offset + data_length)
            else:
                data_slice = slice(offset + 2 + 12 * i + 8,
                                   offset + 2 + 12 * i + 8 + data_length)
            if data_type == ASCII:
                data = self.data[data_slice]
            else:
                if data_type == RATIONAL or data_type == SRATIONAL:
                    l = struct.unpack('%s%d%s'
                                      % (self.byte_order_char, 2 * count,
                                         DATA_TYPE_FORMAT[data_type]),
                                      self.data[data_slice])
                    data = zip(l[0::2], l[1::2])
                else:
                    data = struct.unpack('%s%d%s'
                                         % (self.byte_order_char, count,
                                            DATA_TYPE_FORMAT[data_type]),
                                         self.data[data_slice])
                if count == 1:
                    data, = data
            yield (tag, data)

    def ifd_offsets(self):
        offset = self.first_ifd_offset
        while offset:
            yield offset
            n, = struct.unpack(self.byte_order_char + 'H',
                               self.data[offset:offset + 2])
            sl = slice(offset + 2 + 12 * n, offset + 2 + 12 * n + 2)
            offset, = struct.unpack(self.byte_order_char + 'H', self.data[sl])


TAGS = {
    0x8769: 'ExifIFDPointer',
    0x8825: 'GPSInfoIFDPointer',
    0xa005: 'InteroperabilityIFDPointer',
    0x0100: 'ImageWidth',
    0x0101: 'ImageHeight',
    0x0102: 'BitsPerSample',
    0x0103: 'Compression',
    0x0106: 'PhotometricInterpretation',
    0x0112: 'Orientation',
    0x0115: 'SamplesPerPixel',
    0x011c: 'PlanarConfiguration',
    0x0212: 'YCbCrSubSampling',
    0x0213: 'YCbCrPositioning',
    0x011a: 'XResolution',
    0x011b: 'YResolution',
    0x0128: 'ResolutionUnit',
    0x0111: 'StripOffsets',
    0x0116: 'RowsPerStrip',
    0x0117: 'StripByteCounts',
    0x0201: 'JPEGInterchangeFormat',
    0x0202: 'JPEGInterchangeFormatLength',
    0x012d: 'TransferFunction',
    0x013e: 'WhitePoint',
    0x013f: 'PrimaryChromaticities',
    0x0211: 'YCbCrCoefficients',
    0x0214: 'ReferenceBlackWhite',
    0x0132: 'DateTime',
    0x010e: 'ImageDescription',
    0x010f: 'Make',
    0x0110: 'Model',
    0x0131: 'Software',
    0x0138: 'Artist',
    0x8298: 'Copyright',
    }

EXIF_IFD_TAGS = {
    0x9000: 'ExifVersion',
    0xa000: 'FlashpixVersion',
    0xa001: 'ColorSpace',
    0xa002: 'PixelXDimension',
    0xa003: 'PixelYDimension',
    0x9101: 'ComponentsConfiguration',
    0x9102: 'CompressedBitsPerPixel',
    0x927c: 'MakerNote',
    0x9286: 'UserComment',
    0xa004: 'RelatedSoundFile',
    0x9003: 'DateTimeOriginal',
    0x9004: 'DateTimeDigitized',
    0x9290: 'SubsecTime',
    0x9291: 'SubsecTimeOriginal',
    0x9292: 'SubsecTimeDigitized',
    0x928a: 'ExposureTime',
    0x829d: 'FNumber',
    0x8822: 'ExposureProgram',
    0x8824: 'SpectralSensitivity',
    0x8827: 'ISOSpeedRatings',
    0x8828: 'OECF',
    0x9201: 'ShutterSpeedValue',
    0x9202: 'ApertureValue',
    0x9203: 'BrightnessValue',
    0x9204: 'ExposureBiasValue',
    0x9205: 'MaxApertureValue',
    0x9206: 'SubjectDistance',
    0x9207: 'MeteringMode',
    0x9208: 'LightSource',
    0x9209: 'Flash',
    0x9214: 'SubjectArea',
    0x920a: 'FocalLength',
    0xa20b: 'FlashEnergy',
    0xa20c: 'SpatialFrequencyResponse',
    0xa20e: 'FocalPlaneXResolution',
    0xa20f: 'FocalPlaneYResolution',
    0xa210: 'FocalPlaneResolutionUnit',
    0xa214: 'SubjectLocation',
    0xa215: 'ExposureIndex',
    0xa217: 'SensingMethod',
    0xa300: 'FileSource',
    0xa301: 'SceneType',
    0xa302: 'CFAPattern',
    0xa401: 'CustomRendered',
    0xa402: 'ExposureMode',
    0xa403: 'WhiteBalance',
    0xa404: 'DigitalZoomRatio',
    0xa405: 'FocalLengthIn35mmFilm',
    0xa406: 'SceneCaptureType',
    0xa407: 'GainControl',
    0xa408: 'Contrast',
    0xa409: 'Saturation',
    0xa40a: 'Sharpness',
    0xa40b: 'DeviceSettingDescription',
    0xa40c: 'SubjectDistanceRange',
    0xa420: 'ImageUniqueID',
    }

GPS_INFO_IFD_TAGS = {
    0x0000: 'GPSVersionID',
    0x0001: 'GPSLatitudeRef',
    0x0002: 'GPSLatitude',
    0x0003: 'GPSLongitudeRef',
    0x0004: 'GPSLongitude',
    0x0005: 'GPSAltitudeRef',
    0x0006: 'GPSAltitude',
    0x0007: 'GPSTimeStamp',
    0x0008: 'GPSSatellites',
    0x0009: 'GPSStatus',
    0x000a: 'GPSMeasureMode',
    0x000b: 'GPSDOP',
    0x000c: 'GPSSpeedRef',
    0x000d: 'GPSSpeed',
    0x000e: 'GPSTrackRef',
    0x000f: 'GPSTrack',
    0x0010: 'GPSImgDirectionRef',
    0x0011: 'GPSImgDirection',
    0x0012: 'GPSMapDatum',
    0x0013: 'GPSDestLatitudeRef',
    0x0014: 'GPSDestLatitude',
    0x0015: 'GPSDestLongitudeRef',
    0x0016: 'GPSDestLongitude',
    0x0017: 'GPSDestBearingRef',
    0x0018: 'GPSDestBearing',
    0x0019: 'GPSDestDistanceRef',
    0x001a: 'GPSDestDistance',
    0x001b: 'GPSProcessingMethod',
    0x001c: 'GPSAreaInformation',
    0x001d: 'GPSDateStamp',
    0x001e: 'GPSDifferential',
    }

INTEROPERABILITY_INFO_IFD_TAGS = {
    0x0001: 'InteroperabilityIndex',
}

IFD_POINTER_TAGS = {
    0x8769: EXIF_IFD_TAGS,
    0x8825: GPS_INFO_IFD_TAGS,
    0xa005: INTEROPERABILITY_INFO_IFD_TAGS,
}


def exif(data):
    tiff = TIFF(data)
    result = {}
    for ifd_offset in tiff.ifd_offsets():
        for tag, value in tiff.ifd_tags(ifd_offset):
            if tag in IFD_POINTER_TAGS:
                ifd_tags = IFD_POINTER_TAGS[tag]
                for tag, value in tiff.ifd_tags(value):
                    result[ifd_tags.get(tag, tag)] = value
            else:
                result[TAGS.get(tag, tag)] = value
    return result


def parse_angle(value):
    return sum(n / d for n, d in zip([float(n) / d for n, d in value],
                                     (1, 60, 3600)))


def parse_datetime(value):
    return datetime.datetime.strptime(value.rstrip('\0'), '%Y:%m:%d %H:%M:%S')


CHARSETS = {
    'ASCII': 'ascii',
    'JIS': 'shift_jis',
    'UNICODE': 'utf_8',
    '': 'latin_1'}


def parse_usercomment(value):
    value = ''.join(map(chr, value))
    charset = value[0:8].rstrip('\0')
    if charset in CHARSETS:
        return value[8:].rstrip('\0').decode(CHARSETS[charset])
    else:
        return value


SOI = 0xffd8
APP1 = 0xffe1
SOF0 = 0xffc0
SOF2 = 0xffc2


class JPEG(object):

    def __init__(self, file):
        self.exif = {}
        self.height = self.width = None
        for tag, data in JPEG.chunks(file):
            if tag == APP1 and data[0:6] == 'Exif\0\0':
                self.exif = exif(data[6:])
            elif tag in [SOF0, SOF2]:
                self.height, self.width = struct.unpack('>HH', data[1:5])
        if self.height is None or self.width is None:
            raise SyntaxError, "Missing SOF"

    @classmethod
    def chunks(self, file):
        if struct.unpack('>H', file.read(2)) != (SOI,):
            raise SyntaxError, "Missing SOI header"
        tag, = struct.unpack('>H', file.read(2))
        while tag > 0xff00:
            size, = struct.unpack('>H', file.read(2))
            yield (tag, file.read(size - 2))
            tag, = struct.unpack('>H', file.read(2))
