namespace  comm { namespace  protocal
{
class xdrive_thrift_datagram
{
      TOLUA_TEMPLATE_BIND("TDt IType", __datagram__)

      xdrive_thrift_datagram();
      ~xdrive_thrift_datagram();

      TDt *base();

      static const int MSG_TYPE;

      std::string  hencode(int status = 0, int seq = 0);
      std::string encode();
      int  decode(const char *data, int buf_len);

      std::string to_string() const;
};

$renaming xdrive_thrift_datagram<__dt__,__dt_val__> @ __shortname__

} 
}
