# pip install secretsharing
# https://github.com/blockstack/secret-sharing
from secretsharing import PlaintextToHexSecretSharer as SS
import random
from Crypto.Cipher import AES,PKCS1_OAEP
from Crypto.PublicKey import RSA
import libnum, sympy
from sympy import Symbol
from sympy.solvers import solve
import fractions, primefac

'''
inspect file .pub to find e, n
openssl rsa -pubin -in key-0.pem -text -modulus
'''

def get_rand_bytes(length):
	return "".join([chr(random.randrange(256)) for i in range(length)])

def encrypt(public_key, message):
	"""Encrypt a message with a given public key.
	
	Takes in a public_key generated by Crypto.PublicKey.RSA, which must be of
	size exactly 4096
	"""
	symmetric_key = get_rand_bytes(32)
	msg_header = PKCS1_OAEP.new(public_key).encrypt(symmetric_key)
	assert len(msg_header) == 512
	msg_iv = get_rand_bytes(16)
	msg_body = AES.new(symmetric_key,
			mode=AES.MODE_CFB,
			IV=msg_iv).encrypt(message)
	return msg_header + msg_iv + msg_body

def decrypt(private_key, ciphertext):
	"""Decrypt a message with a given private key.

	Takes in a private_key generated by Crypto.PublicKey.RSA, which must be of
	size exactly 4096

	If the ciphertext is invalid, return None
	"""
	if len(ciphertext) < 512 + 16:
		return None
	msg_header = ciphertext[:512]
	msg_iv = ciphertext[512:512+16]
	msg_body = ciphertext[512+16:]
	try:
		symmetric_key = PKCS1_OAEP.new(private_key).decrypt(msg_header)
	except ValueError:
		return None
	if len(symmetric_key) != 32:
		return None
	return AES.new(symmetric_key,
			mode=AES.MODE_CFB,
			IV=msg_iv).decrypt(msg_body)

def get_privatekay(e, p, q):
	d = long(libnum.invmod(e, (p - 1 ) * (q - 1)))
	private_key = RSA.construct((long(p*q), e, d))
	return private_key

# ------------------------ fermat
def isqrt(n):
	x = n
	y = (x + n // x) // 2
	while y < x:
		x = y
		y = (x + n // x) // 2
	return x

def fermat(n, verbose=True):
	a = isqrt(n) # int(ceil(n**0.5))
	b2 = a*a - n
	b = isqrt(n) # int(b2**0.5)
	count = 0
	while b*b != b2:
		if verbose:
			print('Trying: a=%s b2=%s b=%s' % (a, b2, b))
		a = a + 1
		b2 = a*a - n
		b = isqrt(b2) # int(b2**0.5)
		count += 1
	p=a+b
	q=a-b
	assert n == p * q
	# print 'a=',a
	# print 'b=',b
	# print 'p=',p
	# print 'q=',q
	# print 'pq=',p*q
	return p, q

# ------------------------ wiener
def partial_quotiens(x, y):
	pq = []
	while x != 1:
		pq.append(x / y)
		a = y
		b = x % y
		x = a
		y = b
	return pq

def rational(pq):
	i = len(pq) - 1
	num = pq[i]
	denom = 1
	while i > 0:
		i -= 1
		a = (pq[i] * num) + denom
		b = num
		num = a
		denom = b
	return (num, denom)

def convergents(pq):
	c = []
	for i in range(1, len(pq)):
		c.append(rational(pq[0:i]))
	return c

def phiN(e, d, k):
	return ((e * d) - 1) / k

def wiener_attack(e, n):
	pq = partial_quotiens(e, n)
	c = convergents(pq)
	x = Symbol('x')
	for (k, d) in c:
		if k != 0:
			y = n - phiN(e, d, k) + 1
			roots = solve(x**2 - y*x + n, x)
			if len(roots) == 2:
				p = roots[0]
				q = roots[1]
				if p * q == n:
					break
	return p, q

def decryptFile(filename, e, p, q):
	print 'decrypting message..'
	ciphertext = open(filename,'rb').read()
	private_key = get_privatekay(e, p, q)
	message = decrypt(private_key, ciphertext)
	print message
	print '-----------------'
	return message

def factorKey1():
	print 'factoring key1..'
	n1 = 0xC4FF486B14CD9C37B956F08FF19CA2F83DBA86509CB840CD6A5A95F1352009B18D1D56B4A0FEC0E95A29CA96CAEFAA5DEFF71D6AEB0AD89EEAAD908CEE93582BD71B2CD7DAF709A54B98D163B508D3FD1F0A9709FB69E499D1B8ABC50AF3A4CBAE77C070444933613A452954F91ACDAF461D6A364035920561F7885D30EBDC82BE3560E6428864B9715E1734D013E23DFB8C1DA662F5CE6DA3712402F8DA445D0CA49B9BB1E47ABEEEF58A6385CA3F9EB9D24008B6E68E1DE7C2F12FEA14F7729C248D8DB7D9B85E6279AB68B0517F739D9745BA02F8AABC33819C326116C327396B5716C6895495AE8D3CF60A3B6A11557329383F6D5F414D9E05E87E13D5D7CBF87994C86F1419A8FC969500E36D8570FBE1BC13DF8BFE3888209B0BD684B9265BF7F4E05CF670D8F288E1D82740E9812F9AA68A99B5E569420B38CC1538787EAD253DF53341E3C2697CE76152B02ED437CCE19386E2A13608BFB7B23336356F032C550F1FBC4F8EE00294CBECB03ECE45DFC5F5C115D73ADC988BA297104C81351BB73C2AC01D3ACFC5A814C4947B5758B0193222102C1541F398D2D7B1C2CFDD53A172AA899880F53A8B5C7E6A39E6E408141DF99AE2F6BEFC00B02E2AC4C3AF122BE5097F3231C5B4E607BCA2A78C1F1040AA3C4351DE4B3172E3882C116E5F586DE33CEE9C911875AC196EFB8355D4CDDFE5479B19FA426A25E0EA1891
	p, q = fermat(n1, verbose=False)
	'''
	or can use yafu to find p, q from fermat method
	yafu-x64.exe "@" -batchfile in.bat
	-------------- in.bat --------------
	fermat(0xC4FF486B14CD9C37B956F08FF19CA2F83DBA86509CB840CD6A5A95F1352009B18D1D56B4A0FEC0E95A29CA96CAEFAA5DEFF71D6AEB0AD89EEAAD908CEE93582BD71B2CD7DAF709A54B98D163B508D3FD1F0A9709FB69E499D1B8ABC50AF3A4CBAE77C070444933613A452954F91ACDAF461D6A364035920561F7885D30EBDC82BE3560E6428864B9715E1734D013E23DFB8C1DA662F5CE6DA3712402F8DA445D0CA49B9BB1E47ABEEEF58A6385CA3F9EB9D24008B6E68E1DE7C2F12FEA14F7729C248D8DB7D9B85E6279AB68B0517F739D9745BA02F8AABC33819C326116C327396B5716C6895495AE8D3CF60A3B6A11557329383F6D5F414D9E05E87E13D5D7CBF87994C86F1419A8FC969500E36D8570FBE1BC13DF8BFE3888209B0BD684B9265BF7F4E05CF670D8F288E1D82740E9812F9AA68A99B5E569420B38CC1538787EAD253DF53341E3C2697CE76152B02ED437CCE19386E2A13608BFB7B23336356F032C550F1FBC4F8EE00294CBECB03ECE45DFC5F5C115D73ADC988BA297104C81351BB73C2AC01D3ACFC5A814C4947B5758B0193222102C1541F398D2D7B1C2CFDD53A172AA899880F53A8B5C7E6A39E6E408141DF99AE2F6BEFC00B02E2AC4C3AF122BE5097F3231C5B4E607BCA2A78C1F1040AA3C4351DE4B3172E3882C116E5F586DE33CEE9C911875AC196EFB8355D4CDDFE5479B19FA426A25E0EA1891, 1000)
	EOF
	------------------------------------
	'''
	# p = long(28349223152666012309896421767725787316124897111416473420803849019741154117582482568645254183215552986563114855665416593397403745371086355268654763921803558654340155902194948080056226592560917521612824589013349044205989541259468856602228462903448721105774109966325479530181197156476502473067978072053273437369680433495259118953717909524799086692640103084287064091489681162498108275295255082627807077949841602061428289272700263987438087045434043977981316071156426134695316796020506076336851840708593720052204359360366058549157961154869248835793804817253083037277453771408544063058190126149127240681909811943783388977967)
	# q = long(28349223152666012309896421767725787316124897111416473420803849019741154117582482568645254183215552986563114855665416593397403745371086355268654763921803558654340155902194948080056226592560917521612824589013349044205989541259468856602228462903448721105774109966325479530181197156476502473067978072053273437369680433495259118953717909524799086692640103084287064091489681162498101607280822202773532998098050880803631144514377948079277690787622279940743498439084904702494445241729763146426258407468147831250550239995285695193105630324823153678214290802694619958991541957383815098042054239547145549933872335482492225099839)
	e = long(65537)
	return decryptFile('ciphertext-5.bin', e, p, q)

def factorKey2():
	print 'factoring key2..'
	'''
	found in factordb.com
	or can use yafu to find p, q from rho method
	yafu-x64.exe "@" -batchfile in.bat -rhomax 5000
	-------------- in.bat --------------
	factor(0x86986548C02B2D6B0461A74A09A5EE4EFA07882D5C610BDB14D1BA3044EFFD5570E4C509D116ACA992A342CF52ED0463DB6D4648A3013BA8219C3A72B1998796253DD11ECC536087E6E5BD207C1387AF9DF6BF875AB319556DCC0BAD6A90F017459760EE7D274FE6046E7599385F7607D29ED235477695E3365FC6B9F5270183E9C4C2C118AA676C1D9CBE06864507E4310D85B8CACFF9F5A3EED487B71D2D75B00943D7EDA9AAF5B2BB69271625DE2469D6A7C4F50C4EEAC54B1605793CC0F7FE9167452FF5FEF3647C9EEC8866730732C05DCA4C56F393CA2E61E7D76442822B9DA56D96F67BBA9F6095F761D0F2A3DE62EA8C6FC7AC2FA7B727684947F7640711B700F40A1799D0265EEFE94952B50E5E10B15BEC14CC1664714C6C1FF1C16454F4A912EC19760D80C4759FF3130DA43B13E7967D5CEA526402CF2B566653C0CD5D7D0995357661C0308CBD11AAEB832CA9093DC3981D1FB6B62FD98A883E8D4C1548521C3E2F0BEF76C7220D8093C2BDB1AE017F2E48D0DEFE42CE5713955AE294BEC2B5DA9B81CF9BB1D8CA5E5DCC9BF930EDB7A3F6D2D350D2AA478E01070DBC151D6F9F6DBA473EC001432DE4E2CED4611955F294B3D48631DD51EB7C50A97F5165731D597129D3335F4C994234D89095335C705F075A1BA08A0F5CF383D65CD424524A48A415CE2CA5A34B4287E4EFACB243E68B9C90A3679BEF2757)
	EOF
	------------------------------------
	'''
	p = long(199050626189790903113151725251371951406311367304411013359159100762029303668345459282823483508119186508070350039475140948570888009866572148405365532164833126992414461936781273087675274788769905198546175946505790118332257676994622928414648644875376193656132263418075334807302665038501361680530751104620475935886499714767992159620130246904875540624651891646715835632182355428589610236128648209568297096024509697960196858754170641081387466229916585122877955908862176165344465889280850859817985096316883025515924332365977538735425288433292357532172467247159245727072344354499113900733623716569924461327947462469348798798400461045817375922057805611166274339541877392159201774893120311667898551312256530117094221191204981071357303328506659872809131929265966688409379037586014938643190675726674943253875287765020503118408406103824607730713529079962656130622218633922911733000466212212532871890933508287965723844399784165195088175666883742686183165151553009638524764735387233844317375317153437534933611361683136151569588355535831475925641431859231311079029505004457816932257031352498323214304125608733640306746900473758755832661915903475867854937735150255829715879232213599597863424779218670961633567259935246911742292942052832671549)
	q = long(2758599203)
	e = long(65537)
	return decryptFile('ciphertext-1.bin', e, p, q)

def factorKey3():
	print 'factoring key3..'
	e = long(0x380d01edb6ecc75e51056ef60dec807a8c17356ea6644ecf62c2b85763f79fa65f1b54d4ff283fbb0b0b3e6fa57186c52bea20e096368c194141cded75978bbe14d2709d20145601d0dd6b7e2df0dded42a514d298c68182289b8241aa09afebe7f3d0a187a6545b89a06cee5287e8257264e04bd09683d9b4b3b04f2ea86782d3e379e5014ff616202c78ad9b0801b67eeeeaaf3b43055a6f096c9bfb119f1b57c78c6e4050acf3c9677f93257a2baab9ffbc0f562fc64d468d639db090cdb626101268fbc286c5c9845abafb6c06fc0625904ccf32837fb2fd5d160df8360b33fe2fa55fb43fd4ba0ba69dde44f72f9e06509a636ec8456857597b9a5530b43b6c2f11038c9fce71d5debd7b63c7fb1daf7c84379093b1f9d8f5e1d4ab5e96e487c4ac4cd1629767a559e0fe95699975d3b2969fbc48e6c0529b42e45051ac5ce998b8a7772512dc32c48902a996c3fbd315967be6a4035563088f3bbee79dc324fd083b2e529f2d114bae5e6dea53dde3e518081a4a13e696b50ed8a51bac565353a98a6b841fad798e970150629956a4816b1d7968f65cefe71b192073412cdd69c0c22219a49c5891e636662ae3429ca9c2a3a29a89251674b37c076f66244b41fb228c82568967c0940e454f4974f68d1863f7398ddd6231fae8c7ff6f83faf31b472e75ae26ced598191b0f627dc2759e2a9a860a3e3b03caf68aacbf)
	n = 0x994A5E2C2303B40943D9B744B5709EE601FB5C4AC300CFA44A7608107A74D06AC04963A3F8201FA7801335EDD3F323090425924B74F6AC39EEAFF7B4A6BCAA241533FD5F57505B388668F24D8D65330745CC515EE1B3C96016B399C35EEFEF0612BAFF82761088117B07E25F9263F914981023319165D209C4784BC37A92ED7FECB470317B3FDE5343CDD9AA13794B74831892CF6EA1002D7A3F760F1BB3EDFBF6273B15361127424F1712892E0C6CC759B3C690DA8C6184A90BE6486B8F25C745554C0AAA445764589A5177038A67CD73E66FE1B0D559E0BBBE3E5B8D4AEEF72FFA874CC16110BBC135C3E9928C5FCAE737815F49FB023C64EDA62AD2ED7D0D32249617DC512DC540006C0F059B2FDAEB3B0AE1C2B9615DB7C83B909E222719451736E1F07C3919C3965FD9D003BD8813EC1E9CD540FAF7F70F72FE8F0F544B2CAB51A8A062865AE4F46A0530B7E11A264D717F3CF13B6018D09DE1A0C28EA20CEE2A6711DA5D115FD71C096D115C13F0B5E40D94696C67105C2F709AE5D2FE0AC85847B3C9017ACE7DB2EB00D410D9D2DA7685776A8099472D01791C57810D160ABD6C9E420276320EB11B80A0B2F5722E20E9D8822A1D143C97A63EF81733E52F263E3A7F77B6900BF95DA215544DF51E61ECC468F037A2B39CCF153D984B32A9A4CE757BBB38798CE0B080F503CE1A396D47E14CC41BF18E34EDBD9137EB
	p, q = wiener_attack(e, n)
	
	# p = long(24333562944687516822197571192658754203291290861678417217447438854540594847087766562404339574537862439116548079253289466115128767870577648533973566286797593441730003379848043825634065823911136780045362090360846493427099473619203426216220826743478974241107765471416754913629766068614128278553165309459614540881272639715963742807416312087758332567870818068056326342400589601117982695439948496482753836668023789721452705706258642830333890588979897355741176673670662543132574318628603066958811749579934075668455748590286427527491514861437629540690813171672435522560204943058263324060332232490301430308879676240097644556943)
	# q = long(25699922293123622238012005113928758274338093880738911843144609876290300384447243164527369410936522534026502861166228851341858617366580840945546916656960397913459416157594030359887797479829819533476376181670391998963549074371737295746623468123112547424135047636878302121269250886314724602949616886176008642837449632045010113812032294774060357611189602487961064611234002464905006798590256478016955856378120527444702590839053848988168714049387256070864726124290373739801554166928887083826045058481026363141572007235867367607974662051368481037707609970666363610931674810380477197023311110704572295255843715262143691203301)
	return decryptFile('ciphertext-4.bin', e, p, q)

def factorKey0():
	print 'factoring key0..'
	n = []
	n.append(0xD7AF32B093D6E224BB963A9A7BC873B2E77C6ACE763E7D6C6DD7D1D11182852F684B503DD72E7694FDEC4668AFBF6F90C4AF4662ABEE1C3A33C50EC5C52A8C0A9AAF4D0F3161EBB4EE7622A22FF1FB67B93023D49431306FFC0140191B1077B114CCA884DB4CCDD8D1F7BB131EF321B4907003548161921D293A4263189708BA0755452A66A6DC916188B263010536FD239EBEDA8D877A66DD84CB431F5A62AB908B66B4E64D3E57BFBA338E13B0377C0303D63860755864785A1C8F4B5FB47C6FC4F2A9FD853073230733C68B754B2B480107027333039BB1D84913137E6DFA473E92D4B24AF57E730A4A34F6E01A416F94A8355CCF46954CD26D2503BCEA20903ECD77A01F2684CF1D7C7124B45DEFABD6C2B47F26DC142812C83573C412813F016804E2C12F31CA433DEDD47634BBE3E4935D762AB6E59E72EA0932FF75F18807A8B17A2F6881763CF3028B9E15A5114C06817FB076E05F4D41FA52B9DB79599FF407A1856B4EB4738F1CED340A44070729C2A56AD73B61243B6CA996A20D50548DFCB11D750689AE93471331FE68C22922687F16C48308D3AD74E8C9BFF8C1744C0674D203A56C099D7BEE8EF94D92D9B4EC3D1E9197A0AC49257545FC09E1ED739D6A10ADDA082E5B18F7EAA83E786EE9AD8586070EA65DB4F9B5ABB9394DA32FB74D68C8D4A64EF5C4A12CC29D612264E73D259A3FD688C5567558BEA9)
	n.append(0xC4FF486B14CD9C37B956F08FF19CA2F83DBA86509CB840CD6A5A95F1352009B18D1D56B4A0FEC0E95A29CA96CAEFAA5DEFF71D6AEB0AD89EEAAD908CEE93582BD71B2CD7DAF709A54B98D163B508D3FD1F0A9709FB69E499D1B8ABC50AF3A4CBAE77C070444933613A452954F91ACDAF461D6A364035920561F7885D30EBDC82BE3560E6428864B9715E1734D013E23DFB8C1DA662F5CE6DA3712402F8DA445D0CA49B9BB1E47ABEEEF58A6385CA3F9EB9D24008B6E68E1DE7C2F12FEA14F7729C248D8DB7D9B85E6279AB68B0517F739D9745BA02F8AABC33819C326116C327396B5716C6895495AE8D3CF60A3B6A11557329383F6D5F414D9E05E87E13D5D7CBF87994C86F1419A8FC969500E36D8570FBE1BC13DF8BFE3888209B0BD684B9265BF7F4E05CF670D8F288E1D82740E9812F9AA68A99B5E569420B38CC1538787EAD253DF53341E3C2697CE76152B02ED437CCE19386E2A13608BFB7B23336356F032C550F1FBC4F8EE00294CBECB03ECE45DFC5F5C115D73ADC988BA297104C81351BB73C2AC01D3ACFC5A814C4947B5758B0193222102C1541F398D2D7B1C2CFDD53A172AA899880F53A8B5C7E6A39E6E408141DF99AE2F6BEFC00B02E2AC4C3AF122BE5097F3231C5B4E607BCA2A78C1F1040AA3C4351DE4B3172E3882C116E5F586DE33CEE9C911875AC196EFB8355D4CDDFE5479B19FA426A25E0EA1891)
	n.append(0x86986548C02B2D6B0461A74A09A5EE4EFA07882D5C610BDB14D1BA3044EFFD5570E4C509D116ACA992A342CF52ED0463DB6D4648A3013BA8219C3A72B1998796253DD11ECC536087E6E5BD207C1387AF9DF6BF875AB319556DCC0BAD6A90F017459760EE7D274FE6046E7599385F7607D29ED235477695E3365FC6B9F5270183E9C4C2C118AA676C1D9CBE06864507E4310D85B8CACFF9F5A3EED487B71D2D75B00943D7EDA9AAF5B2BB69271625DE2469D6A7C4F50C4EEAC54B1605793CC0F7FE9167452FF5FEF3647C9EEC8866730732C05DCA4C56F393CA2E61E7D76442822B9DA56D96F67BBA9F6095F761D0F2A3DE62EA8C6FC7AC2FA7B727684947F7640711B700F40A1799D0265EEFE94952B50E5E10B15BEC14CC1664714C6C1FF1C16454F4A912EC19760D80C4759FF3130DA43B13E7967D5CEA526402CF2B566653C0CD5D7D0995357661C0308CBD11AAEB832CA9093DC3981D1FB6B62FD98A883E8D4C1548521C3E2F0BEF76C7220D8093C2BDB1AE017F2E48D0DEFE42CE5713955AE294BEC2B5DA9B81CF9BB1D8CA5E5DCC9BF930EDB7A3F6D2D350D2AA478E01070DBC151D6F9F6DBA473EC001432DE4E2CED4611955F294B3D48631DD51EB7C50A97F5165731D597129D3335F4C994234D89095335C705F075A1BA08A0F5CF383D65CD424524A48A415CE2CA5A34B4287E4EFACB243E68B9C90A3679BEF2757)
	n.append(0x994A5E2C2303B40943D9B744B5709EE601FB5C4AC300CFA44A7608107A74D06AC04963A3F8201FA7801335EDD3F323090425924B74F6AC39EEAFF7B4A6BCAA241533FD5F57505B388668F24D8D65330745CC515EE1B3C96016B399C35EEFEF0612BAFF82761088117B07E25F9263F914981023319165D209C4784BC37A92ED7FECB470317B3FDE5343CDD9AA13794B74831892CF6EA1002D7A3F760F1BB3EDFBF6273B15361127424F1712892E0C6CC759B3C690DA8C6184A90BE6486B8F25C745554C0AAA445764589A5177038A67CD73E66FE1B0D559E0BBBE3E5B8D4AEEF72FFA874CC16110BBC135C3E9928C5FCAE737815F49FB023C64EDA62AD2ED7D0D32249617DC512DC540006C0F059B2FDAEB3B0AE1C2B9615DB7C83B909E222719451736E1F07C3919C3965FD9D003BD8813EC1E9CD540FAF7F70F72FE8F0F544B2CAB51A8A062865AE4F46A0530B7E11A264D717F3CF13B6018D09DE1A0C28EA20CEE2A6711DA5D115FD71C096D115C13F0B5E40D94696C67105C2F709AE5D2FE0AC85847B3C9017ACE7DB2EB00D410D9D2DA7685776A8099472D01791C57810D160ABD6C9E420276320EB11B80A0B2F5722E20E9D8822A1D143C97A63EF81733E52F263E3A7F77B6900BF95DA215544DF51E61ECC468F037A2B39CCF153D984B32A9A4CE757BBB38798CE0B080F503CE1A396D47E14CC41BF18E34EDBD9137EB)
	n.append(0xA9DFFBCDF808E4A5120B876D4BE077CEF21B6EF3BBCCDAE77B6AFC988EA068CAD52C6E7D1797049394CAAEE701E916B3D192C6FC8F8AB2C8A0BCDC75CFB1C436A914C128046B889AEB5F1C89852856CAD179A0958A4AEB87BA778EA62187AD1931D5BDCF85D57361FD2941A076EA9B3652110287755E663E679892B4FF0519042B0B3A85AA99F623A1037D503B245CF3205C3C5B24139B3ABF0881FBC1B0F7E03444149F69427FD78CDBC75B634A5160E9B2AADBFD9CFD6150AB0ACE72DD1D95E1D884153CBE9DD62458745A0FE95014E89F263A9730FF2205B108E3985BB9DA9A1B68B4AE1D52CEC2B3A5320E02392E9E8B802D190DE6E4F75388C3FAFDB2BA58904ECEAA613C3D67D81EDE381A0F15A2822BD1A5A1854DF38AEA7D32E6CF8C38D8D6A8DAF384BEFC5EE06C9BE1A4B2216B690B28DFAAEBD9D47B3D96FDDD96114DC6DF9B1EB21343098EF9E6540FBAC0C19A63CDAF6E4528AE41D212E50DAB72FF4529B042EC22DD8D61166D29548559ED7DE469391781444BAEE28F3ECBED79169A7134DA785D476533ACE2FFE3AEE5B9501549A8061AD50B352D01735DFB4CA7D4D0BF759C9DBCBB1BA4793A30238F959AD033B5691920B3E2FC793FE154EE9F6EBC5D64744B518A41E26803D11F1FDA6D223904C26054B4C685E3640DA0E1F4DA6445B55757AC7E4E18C938168C1D8C64F31EB11E4AAA09D0C94FCA9973)
	n.append(0x88EF837570C4161F5EF7D6E65DEAFB9840CFFAE5F3377D7B2C4FA8EE99286FDA86D1DD77AEC9A7D9751328C0D0DB4481F8A108B4D844262EA1FB8BF02AA44DBA0F9C02BAF186BAC37E02314C48277803B088C2921076B155C4882CF4C2397796959EDF22AF6A2FF769CA4668F370EEA104AC006DF3FEAD69E1B7C00B8D4EA0B8E99F904C7B66FAD4CEA031091B66A21373C0CC64D2151D8274F128D183A7F3D697965F1590F3F2656259FDA9BE417510949DAB2163C5F450D662A899FCAA31344AD0DECD558FA3E9F9247A23FE451C8F846ACAD19360E66720909F405064F576B6C925A081D4865F7BC861D51101C33D695656B33D164E38948234DB1CDC0FBF8608AFF64F67DDBAF3E3EAD882D8AB69916DD6B922CEC62F3D53567B0E644F990ADD24B22D3021178DA47355BDF1714CE142F98D03DAF7B525D0C6AEBF42F2F5E9352584BA503F1771BF5B2ED7F77023C3C82E8AEFC79D3C22D177B3F6E3D5E399F586B4041CBA5E4CD66E30FE9666DF9FC6216F2BA1D0FF002FA1D6F1CA787A3130A6A5CA929FA737C8FCD86C753709BC23F54EDDD6C1FC6D121932E900F4BE24200329432BACF3AA8E6FC9E87A226457DFE24745FC7C969390F992F999EA4920CFCCC4C47C06B9AEBABAB4C91F14D8FF85E27576F0A027CA70093C185C008B27E8243121551E4705FD46C3561485ABF2FBAA0FC28A87871FE2E3F5AFA30527)
	n.append(0xBC0D4DD9ED44C44C2173ABD3B025401B366816D913F7B4271B71ABCDED21AB0D04C2FC577A313B794275845DBB89E8151CF4BD3825E9240C88EB93A824CAA8B0B563960FFCB12FBCAFCD9D38FBDF87B134395D0EA316186BEAF2470A535A1DA3529C005CB9062F0D43EB8E7BF4CD79425A6CAB65A15C905713ABCEDBF4A715C46465BECBBA9ED60FD77BF82F035D8A394C56F13898834B277C6749261A9C95B22574C1F7781550345588CF2FF1D22EAEB1137AEE4D41F6E288759844A4EB8E8CBDFAEA1776D3C45E7551C9924317D0EFE36A686AFB3AC8A12AB809A3DEEE27D7F69F26B70B97CD1ED51426E489E804881DCAE802FBA751C3F83B6983CFCB4C30C966CA92E7BF08874B2848E098F021F183AE839BE30191E3BCD2CE38325E3991C6E733BF00CF3F60AAEF2B7EBD0554FB0C980A6F62DB59974E7F3CE46AFB24E43E107EC8D1CC0E772F997FF0C5A602FA8BCD0CBBF78CC2D1A84903A3CC00B397858C02C28F7C0707E66D6DC0DE2CE747D99DC4038BDD924CF3C534BCEC6DCF3D4F0247E30875F39AF7AB0FDA69FCA12D7104C51BF6D66AFF2D12338FFBF51E243ADE078DE6CC1930F872C3AD91D8F822668E56D352C0156E513033EA20C0F163D558B69119734684F98CF789DF72F8C534D008A535C9DAFEBE8774140ADC0C53EEB021852EC282B7BDDCE58C9FFB87A7B4F20B91BFD04ED84EA6566BC397F1D9)
	n.append(0xB7D5A8CCD362A3F4691641EE9176E4D025159AD60A427A7E21343ACEA9EF3F96FA1D70460A504A9C78ACF899DC5F42EC55D00078343B40F9EEEAF5740BD8BE047F66CC01AD7DF6D66A8DD42265A6FF87E8CE168C9A18465002A8E6BA5BC4F108D6E70BB1FF2646492F9C154ADEC571153178606C07299664D3EC7EB1F1301F01D13B3865DB6FA6D27D61667C42C16E764E03F312017109B19A7F9EEDD00A6B082F35BC4399F76D646416A9A40E7C5A2774CF84E9C0D978F316FC95BF391C1B1A4E6753DC4C2BA31AF2DE8A485E65408F63D34B17318C1B83D437964AE047842BC73C4A020888B7988755C7E64F35E8FE7F812217FDFB87F815995815343409B5B6BED6869181F72E0737F4F98456F0C6A084CAE14960E44A091714C4941AB4A37A657B241795B7315A6ED24C038E7ECCE82586810D0FB33B503C2A0F72377DB68A02F0FD1E20287155DF960D3D0DD33675F5A4788BCEA886BD64AAA984DB29045AE886C38C61671B629DE16A743F6FBABB5E6E7FB7A577CD6628757C71469555B9B0517FB4ED115269ED7367B30BD0B1782D19879D7BFCBE33336D070A4BD75E86C90E171409E69B867BFE1BE1537966BE6AC20702457FC04E150AC2F3BF33F4181128690899C976ACF7B6141E9F59176BB0B6F9A52066C79BF669C539714A389136274785593F5AE3BB3AF2EFFCB47F4A45BA72A5117FA89C4173C79D663E99)
	n.append(0xCCD36579389BE5198DDE695C2D97B7EFCC04E332161AC60F82DAC6AE33BB96DD885713915AF2E997B1FDC307673560A3F9FE1935AD3B2A08DFFA55C8D743CDCC9E6528E43FC0BD030CB1B49E12E42888C71801E072B8DDD345A0A28A76CAC3AF17574768E4A66A8E07D9658FFF1AD9DBBA618588C6C4CBC342A786DE733A7D0BDB1F08E48CBAD45865ABCC4AC68DB2A1E3A14F159ADD984EB83CB9241BAB797F477931869BD36F42324E88541A7096ECB5895644B411E199E21CCE30B835256D555B613185583EEFDC27BA3883518C843F4044C309E39C7661CF149C3C0E0F65659544681803FAFBD372955A878DCBB344F38D4CB39DA21A46FC8C79FB39B619A8C4BAAC769106ADDB00742171C44509329FA7673A8178574E5F5D6A1C6B9DB39E25F80AE7937A63E4609AC4F9A3E82C6A3B8FB12927FFC5BA87B256A3F3916AD8B2DDA4B837BF6FA9F905D2D62C669F9B407BC4C67C4582544EBB61E1B077F0446895F58891E6A90460F7F09981BF3BB57D24CED44BB6CB31859D159F100CC35A1E123417DAE4823B374A25DCCE3F176AF21125CF94898576741155086782915EE6B7BE7C3A415FB7C3DCF83C6AD4B93E5846ED3955B6D8F2DD5145C15FF9195255DB8279CDC6D935FE727FE39DF02FBA31B6AAC52FB605F1CEEC30FAFFA7324D1FB2A1AD5B325C48B35CD962130ED6DA64A1C172E7863D505411592B8665D7)
	n.append(0xB17ACF77309DCCDCF05A4259212EE3B148B24E52FD39AAD9CB558CAA4C49A35BED6904037A065F92F3AFFE60DC0123F7C79F1FD52CF8FCB03095E33CCEE9BE8D55796B610077FD06DE336CD2553F0695D809BF0EEEABCEA5085387FA2670DC81B40F4334A2093446C5E53635A7B7FB3D1561A62D91B9669361294B4E68CB1548D9C48DF3EF4DA9A9B3C8EEDD4F9901C3B29F5593DB28023AA7C39400D21A53D7CD014F37D1687C7A7C7F3598FFD7D024941BF62806A92368D73418C05AAA67145D17306DEC22BE5E35473B83D9A6B71ADE5ABC3440D6E9DA0D5A122AD11DEACC45C5D2124755F1A60C919EF7EF4220A1ED253EB1ADA0DE0308681C3D0F558DEA7DE1E396430782A1DDA11B44E1D6A11922E66D77285301E212C2CDA17709008CBE138AA6C9EE152001700D3F2BF72DD8B168F9B6764F5BF9E7E736D4FB9B4053BF5E205D7F85404FAE20AA9AB5131E8EDC17DD1E134B8343F080AE05328925947612EEAF4FB4438C0CF82B6C938FEFEBF8583EDA54494858D033F6AF03FB52F8C02EC40C6F1041F9195499CE3BCA7BF6924631ED3691E976707ED3E701B7637AE3C8B84DF5B2864A7283C6B7BBCADE2C0E29815F930506E472DCF3E4C97890F91BF9FE224E4C2E75325907228DCDA9D7CCE17872540C4E2E99FCE1F91A755F2372CFC71808E779F4090671B00E88B7B7A45DD304A81CB04B7A18F4567ED77305)
	for i in range(10):
		for j in range(i+1, 10):
			gcd = fractions.gcd(n[i], n[j])
			if gcd != 1:
				e = long(65537)
				q = n[i]/gcd
				p = gcd
				return decryptFile('ciphertext-3.bin', e, p, q)

if __name__=="__main__":
	message1 = factorKey1().split('\n')
	#exit()
	message2 = factorKey2().split('\n')
	#exit()
	message3 = factorKey3().split('\n')
	#exit()
	message4 = factorKey0().split('\n')
	#exit()

	print SS.recover_secret([message1[1], message2[1], message3[1], message4[1]]), '\n-----------'
	print SS.recover_secret([message1[2], message2[2], message3[2], message4[2]]), '\n-----------'
	print SS.recover_secret([message1[3], message2[3], message3[3], message4[3]]), '\n-----------'
	print SS.recover_secret([message1[4], message2[4], message3[4], message4[4]]), '\n-----------'