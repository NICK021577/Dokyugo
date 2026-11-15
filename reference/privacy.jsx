const imgLogoMark = "https://www.figma.com/api/mcp/asset/7c51a0bc-a700-4f2f-adcb-d90f83c281b7.svg";
const imgRedWedge = "https://www.figma.com/api/mcp/asset/04698ed4-fe4f-46fe-8673-61a38a44f299.svg";
const imgSun = "https://www.figma.com/api/mcp/asset/ad5db4ac-5c6f-4868-bdef-8b4d2408fc0e.svg";
const imgVector = "https://www.figma.com/api/mcp/asset/03648b30-4d96-4183-b5df-044f7c1d80e8.svg";
const imgVector1 = "https://www.figma.com/api/mcp/asset/d9f1e4b5-5c41-4f05-a033-790bb30f6658.svg";
const imgVector2 = "https://www.figma.com/api/mcp/asset/5409e929-8f0a-4670-aea9-086fcd2e16b6.svg";
const imgSun1 = "https://www.figma.com/api/mcp/asset/cceffc8b-660f-4844-8ee3-b1bc45016af3.svg";

export default function PrivacyNotice() {
  return (
    <div className="bg-[var(--white,white)] content-stretch flex flex-col items-start relative size-full" data-node-id="12:870" data-name="Privacy notice">
      <div className="content-stretch flex flex-col items-start relative shrink-0 w-full" data-node-id="12:871" data-name="Header">
        <div className="bg-[var(--white,white)] content-stretch flex h-[76px] items-center justify-between px-[48px] relative shrink-0 w-full" data-node-id="12:872" data-name="Nav">
          <div className="content-stretch flex gap-[10px] items-center relative shrink-0" data-node-id="12:873" data-name="Logo">
            <div className="relative shrink-0 size-[32px]" data-node-id="12:874" data-name="Logo mark">
              <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgLogoMark} />
            </div>
            <p className="[word-break:break-word] font-['Public_Sans:ExtraBold'] font-extrabold leading-[normal] relative shrink-0 text-[22px] text-[color:var(--ink,#1b2640)] whitespace-nowrap" data-node-id="12:878">
              DokyuGo
            </p>
          </div>
          <div className="content-stretch flex gap-[30px] items-center relative shrink-0" data-node-id="12:879" data-name="Links">
            <p className="[word-break:break-word] font-['Public_Sans:SemiBold'] font-semibold leading-[normal] relative shrink-0 text-[17px] text-[color:var(--ink,#1b2640)] whitespace-nowrap" data-node-id="12:880">
              Documents
            </p>
            <p className="[word-break:break-word] font-['Public_Sans:SemiBold'] font-semibold leading-[normal] relative shrink-0 text-[17px] text-[color:var(--ink,#1b2640)] whitespace-nowrap" data-node-id="12:881">
              How it works
            </p>
            <p className="[text-underline-position:from-font] [word-break:break-word] decoration-from-font decoration-solid font-['Public_Sans:SemiBold'] font-semibold leading-[normal] relative shrink-0 text-[17px] text-[color:var(--ink,#1b2640)] underline whitespace-nowrap" data-node-id="12:882">
              Privacy
            </p>
            <p className="[word-break:break-word] font-['Public_Sans:SemiBold'] font-semibold leading-[normal] relative shrink-0 text-[17px] text-[color:var(--ink,#1b2640)] whitespace-nowrap" data-node-id="12:883">
              Log in
            </p>
            <div className="bg-[var(--ink,#1b2640)] content-stretch flex h-[40px] items-center justify-center px-[16px] relative rounded-[10px] shrink-0" data-node-id="12:884" data-name="Button/Book a slot">
              <p className="[word-break:break-word] font-['Public_Sans:Bold'] font-bold leading-[normal] relative shrink-0 text-[15px] text-[color:var(--white,white)] whitespace-nowrap" data-node-id="12:885">
                Book a slot
              </p>
            </div>
          </div>
        </div>
        <div className="content-stretch flex h-[4px] items-start relative shrink-0 w-full" data-node-id="12:886" data-name="Flag stripe">
          <div className="bg-[var(--blue\/600,#3c62b8)] flex-[1_0_0] h-full min-w-px relative" data-node-id="12:887" data-name="stripe" />
          <div className="bg-[var(--yellow\/400,#f2c94c)] flex-[1_0_0] h-full min-w-px relative" data-node-id="12:888" data-name="stripe" />
          <div className="bg-[var(--red\/600,#c9485a)] flex-[1_0_0] h-full min-w-px relative" data-node-id="12:889" data-name="stripe" />
        </div>
      </div>
      <div className="bg-[var(--blue\/600,#3c62b8)] content-stretch flex flex-col gap-[14px] items-start overflow-clip pb-[96px] pt-[56px] px-[88px] relative shrink-0 w-full" data-node-id="12:890" data-name="Page header">
        <div className="absolute h-[80px] left-0 top-[172px] w-[1280px]" data-node-id="12:891" data-name="Red wedge">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgRedWedge} />
        </div>
        <div className="absolute left-[980px] size-[300px] top-[-60px]" data-node-id="12:893" data-name="Sun">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgSun} />
        </div>
        <p className="[word-break:break-word] font-['Public_Sans:ExtraBold'] font-extrabold leading-[56px] relative shrink-0 text-[52px] text-[color:var(--white,white)] tracking-[-1.04px] w-[900px]" data-node-id="12:896">
          Privacy notice
        </p>
        <p className="[word-break:break-word] font-['Public_Sans:Regular'] font-normal leading-[30px] relative shrink-0 text-[20px] text-[color:var(--hero-text,#eaf0fd)] w-[720px]" data-node-id="12:897">
          Last updated [DATE]
        </p>
      </div>
      <div className="content-stretch flex gap-[72px] items-start pb-[88px] pt-[56px] px-[88px] relative shrink-0 w-full" data-node-id="12:898" data-name="Content">
        <div className="content-stretch flex flex-col gap-[6px] items-start relative shrink-0 w-[281px]" data-node-id="12:899" data-name="On this page">
          <div className="content-stretch flex items-start px-[12px] py-[10px] relative shrink-0 w-full" data-node-id="12:900" data-name="Link">
            <p className="[word-break:break-word] font-['Public_Sans:SemiBold'] font-semibold leading-[normal] relative shrink-0 text-[17px] text-[color:var(--ink,#1b2640)] whitespace-nowrap" data-node-id="12:901">
              What we collect
            </p>
          </div>
          <div className="content-stretch flex items-start px-[12px] py-[10px] relative shrink-0 w-full" data-node-id="12:902" data-name="Link">
            <p className="[word-break:break-word] font-['Public_Sans:SemiBold'] font-semibold leading-[normal] relative shrink-0 text-[17px] text-[color:var(--ink,#1b2640)] whitespace-nowrap" data-node-id="12:903">
              Why we collect it
            </p>
          </div>
          <div className="content-stretch flex items-start px-[12px] py-[10px] relative shrink-0 w-full" data-node-id="12:904" data-name="Link">
            <p className="[word-break:break-word] font-['Public_Sans:SemiBold'] font-semibold leading-[normal] relative shrink-0 text-[17px] text-[color:var(--ink,#1b2640)] whitespace-nowrap" data-node-id="12:905">
              Who can see it
            </p>
          </div>
          <div className="content-stretch flex items-start px-[12px] py-[10px] relative shrink-0 w-full" data-node-id="12:906" data-name="Link">
            <p className="[word-break:break-word] font-['Public_Sans:SemiBold'] font-semibold leading-[normal] relative shrink-0 text-[17px] text-[color:var(--ink,#1b2640)] whitespace-nowrap" data-node-id="12:907">
              How long we keep it
            </p>
          </div>
          <div className="content-stretch flex items-start px-[12px] py-[10px] relative shrink-0 w-full" data-node-id="12:908" data-name="Link">
            <p className="[word-break:break-word] font-['Public_Sans:SemiBold'] font-semibold leading-[normal] relative shrink-0 text-[17px] text-[color:var(--ink,#1b2640)] whitespace-nowrap" data-node-id="12:909">
              Your rights
            </p>
          </div>
          <div className="content-stretch flex items-start px-[12px] py-[10px] relative shrink-0 w-full" data-node-id="12:910" data-name="Link">
            <p className="[word-break:break-word] font-['Public_Sans:SemiBold'] font-semibold leading-[normal] relative shrink-0 text-[17px] text-[color:var(--ink,#1b2640)] whitespace-nowrap" data-node-id="12:911">
              Contact
            </p>
          </div>
        </div>
        <div className="[word-break:break-word] content-stretch flex flex-col gap-[44px] items-start relative shrink-0 w-[660px]" data-node-id="12:912" data-name="Sections">
          <div className="content-stretch flex flex-col gap-[12px] items-start relative shrink-0 w-full" data-node-id="12:913" data-name="Section/What we collect">
            <p className="font-['Public_Sans:ExtraBold'] font-extrabold leading-[normal] relative shrink-0 text-[28px] text-[color:var(--ink,#1b2640)] tracking-[-0.56px] whitespace-nowrap" data-node-id="12:914">
              What we collect
            </p>
            <p className="font-['Public_Sans:Regular'] font-normal leading-[29px] min-w-full relative shrink-0 text-[18px] text-[color:var(--muted,#4a5578)] w-[min-content]" data-node-id="12:915">
              Your last name, first name, and middle name, your mobile number, your email address, your password (stored in scrambled form), the document you book, and your appointment date and time. We do not collect ID photos, payment details, or uploaded documents.
            </p>
          </div>
          <div className="content-stretch flex flex-col gap-[12px] items-start relative shrink-0 w-full" data-node-id="12:916" data-name="Section/Why we collect it">
            <p className="font-['Public_Sans:ExtraBold'] font-extrabold leading-[normal] relative shrink-0 text-[28px] text-[color:var(--ink,#1b2640)] tracking-[-0.56px] whitespace-nowrap" data-node-id="12:917">
              Why we collect it
            </p>
            <p className="font-['Public_Sans:Regular'] font-normal leading-[29px] min-w-full relative shrink-0 text-[18px] text-[color:var(--muted,#4a5578)] w-[min-content]" data-node-id="12:918">
              To create your account, schedule your appointment, assign your queue number, and send you a reminder the day before.
            </p>
          </div>
          <div className="content-stretch flex flex-col gap-[12px] items-start relative shrink-0 w-full" data-node-id="12:919" data-name="Section/Who can see it">
            <p className="font-['Public_Sans:ExtraBold'] font-extrabold leading-[normal] relative shrink-0 text-[28px] text-[color:var(--ink,#1b2640)] tracking-[-0.56px] whitespace-nowrap" data-node-id="12:920">
              Who can see it
            </p>
            <p className="font-['Public_Sans:Regular'] font-normal leading-[29px] min-w-full relative shrink-0 text-[18px] text-[color:var(--muted,#4a5578)] w-[min-content]" data-node-id="12:921">
              Barangay staff on duty see the bookings for the day. Administrators manage accounts. Your mobile number is sent to our SMS provider only to deliver reminders. We do not sell your information.
            </p>
          </div>
          <div className="content-stretch flex flex-col gap-[12px] items-start relative shrink-0 w-full" data-node-id="12:922" data-name="Section/How long we keep it">
            <p className="font-['Public_Sans:ExtraBold'] font-extrabold leading-[normal] relative shrink-0 text-[28px] text-[color:var(--ink,#1b2640)] tracking-[-0.56px] whitespace-nowrap" data-node-id="12:923">
              How long we keep it
            </p>
            <p className="font-['Public_Sans:Regular'] font-normal leading-[29px] min-w-full relative shrink-0 text-[18px] text-[color:var(--muted,#4a5578)] w-[min-content]" data-node-id="12:924">
              [RETENTION PERIOD TO CONFIRM]. You can ask us to delete your account at any time.
            </p>
          </div>
          <div className="content-stretch flex flex-col gap-[12px] items-start relative shrink-0 w-full" data-node-id="12:925" data-name="Section/Your rights">
            <p className="font-['Public_Sans:ExtraBold'] font-extrabold leading-[normal] relative shrink-0 text-[28px] text-[color:var(--ink,#1b2640)] tracking-[-0.56px] whitespace-nowrap" data-node-id="12:926">
              Your rights
            </p>
            <p className="font-['Public_Sans:Regular'] font-normal leading-[29px] min-w-full relative shrink-0 text-[18px] text-[color:var(--muted,#4a5578)] w-[min-content]" data-node-id="12:927">
              Under the Data Privacy Act of 2012 (Republic Act No. 10173), you may ask to see, correct, or delete your information, and object to how it is used.
            </p>
          </div>
          <div className="content-stretch flex flex-col gap-[12px] items-start relative shrink-0 w-full" data-node-id="12:928" data-name="Section/Contact">
            <p className="font-['Public_Sans:ExtraBold'] font-extrabold leading-[normal] relative shrink-0 text-[28px] text-[color:var(--ink,#1b2640)] tracking-[-0.56px] whitespace-nowrap" data-node-id="12:929">
              Contact
            </p>
            <p className="font-['Public_Sans:Regular'] font-normal leading-[29px] min-w-full relative shrink-0 text-[18px] text-[color:var(--muted,#4a5578)] w-[min-content]" data-node-id="12:930">
              [BARANGAY DATA PROTECTION CONTACT]
            </p>
          </div>
        </div>
      </div>
      <div className="h-[12px] overflow-clip relative shrink-0 w-full" data-node-id="12:931" data-name="Weave strip">
        <div className="absolute inset-[0_99.22%_0_-0.94%]" data-node-id="12:932" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_98.44%_0_-0.16%]" data-node-id="12:933" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_97.66%_0_0.63%]" data-node-id="12:934" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_96.88%_0_1.41%]" data-node-id="12:935" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_96.09%_0_2.19%]" data-node-id="12:936" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_95.31%_0_2.97%]" data-node-id="12:937" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_94.53%_0_3.75%]" data-node-id="12:938" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_93.75%_0_4.53%]" data-node-id="12:939" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_92.97%_0_5.31%]" data-node-id="12:940" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_92.19%_0_6.09%]" data-node-id="12:941" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_91.41%_0_6.88%]" data-node-id="12:942" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_90.63%_0_7.66%]" data-node-id="12:943" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_89.84%_0_8.44%]" data-node-id="12:944" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_89.06%_0_9.22%]" data-node-id="12:945" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_88.28%_0_10%]" data-node-id="12:946" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_87.5%_0_10.78%]" data-node-id="12:947" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_86.72%_0_11.56%]" data-node-id="12:948" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_85.94%_0_12.34%]" data-node-id="12:949" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_85.16%_0_13.13%]" data-node-id="12:950" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_84.38%_0_13.91%]" data-node-id="12:951" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_83.59%_0_14.69%]" data-node-id="12:952" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_82.81%_0_15.47%]" data-node-id="12:953" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_82.03%_0_16.25%]" data-node-id="12:954" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_81.25%_0_17.03%]" data-node-id="12:955" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_80.47%_0_17.81%]" data-node-id="12:956" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_79.69%_0_18.59%]" data-node-id="12:957" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_78.91%_0_19.38%]" data-node-id="12:958" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_78.13%_0_20.16%]" data-node-id="12:959" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_77.34%_0_20.94%]" data-node-id="12:960" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_76.56%_0_21.72%]" data-node-id="12:961" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_75.78%_0_22.5%]" data-node-id="12:962" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute bottom-0 left-[23.28%] right-3/4 top-0" data-node-id="12:963" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_74.22%_0_24.06%]" data-node-id="12:964" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_73.44%_0_24.84%]" data-node-id="12:965" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_72.66%_0_25.62%]" data-node-id="12:966" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_71.88%_0_26.41%]" data-node-id="12:967" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_71.09%_0_27.19%]" data-node-id="12:968" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_70.31%_0_27.97%]" data-node-id="12:969" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_69.53%_0_28.75%]" data-node-id="12:970" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_68.75%_0_29.53%]" data-node-id="12:971" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_67.97%_0_30.31%]" data-node-id="12:972" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_67.19%_0_31.09%]" data-node-id="12:973" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_66.41%_0_31.87%]" data-node-id="12:974" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_65.63%_0_32.66%]" data-node-id="12:975" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_64.84%_0_33.44%]" data-node-id="12:976" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_64.06%_0_34.22%]" data-node-id="12:977" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_63.28%_0_35%]" data-node-id="12:978" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_62.5%_0_35.78%]" data-node-id="12:979" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_61.72%_0_36.56%]" data-node-id="12:980" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_60.94%_0_37.34%]" data-node-id="12:981" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_60.16%_0_38.13%]" data-node-id="12:982" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_59.38%_0_38.91%]" data-node-id="12:983" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_58.59%_0_39.69%]" data-node-id="12:984" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_57.81%_0_40.47%]" data-node-id="12:985" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_57.03%_0_41.25%]" data-node-id="12:986" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_56.25%_0_42.03%]" data-node-id="12:987" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_55.47%_0_42.81%]" data-node-id="12:988" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_54.69%_0_43.59%]" data-node-id="12:989" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_53.91%_0_44.38%]" data-node-id="12:990" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_53.13%_0_45.16%]" data-node-id="12:991" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_52.34%_0_45.94%]" data-node-id="12:992" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_51.56%_0_46.72%]" data-node-id="12:993" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_50.78%_0_47.5%]" data-node-id="12:994" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute bottom-0 left-[48.28%] right-1/2 top-0" data-node-id="12:995" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_49.22%_0_49.06%]" data-node-id="12:996" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_48.44%_0_49.84%]" data-node-id="12:997" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_47.66%_0_50.63%]" data-node-id="12:998" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_46.88%_0_51.41%]" data-node-id="12:999" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_46.09%_0_52.19%]" data-node-id="12:1000" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_45.31%_0_52.97%]" data-node-id="12:1001" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_44.53%_0_53.75%]" data-node-id="12:1002" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_43.75%_0_54.53%]" data-node-id="12:1003" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_42.97%_0_55.31%]" data-node-id="12:1004" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_42.19%_0_56.09%]" data-node-id="12:1005" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_41.41%_0_56.88%]" data-node-id="12:1006" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_40.63%_0_57.66%]" data-node-id="12:1007" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_39.84%_0_58.44%]" data-node-id="12:1008" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_39.06%_0_59.22%]" data-node-id="12:1009" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_38.28%_0_60%]" data-node-id="12:1010" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_37.5%_0_60.78%]" data-node-id="12:1011" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_36.72%_0_61.56%]" data-node-id="12:1012" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_35.94%_0_62.34%]" data-node-id="12:1013" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_35.16%_0_63.13%]" data-node-id="12:1014" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_34.38%_0_63.91%]" data-node-id="12:1015" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_33.59%_0_64.69%]" data-node-id="12:1016" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_32.81%_0_65.47%]" data-node-id="12:1017" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_32.03%_0_66.25%]" data-node-id="12:1018" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_31.25%_0_67.03%]" data-node-id="12:1019" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_30.47%_0_67.81%]" data-node-id="12:1020" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_29.69%_0_68.59%]" data-node-id="12:1021" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_28.91%_0_69.38%]" data-node-id="12:1022" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_28.13%_0_70.16%]" data-node-id="12:1023" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_27.34%_0_70.94%]" data-node-id="12:1024" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_26.56%_0_71.72%]" data-node-id="12:1025" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_25.78%_0_72.5%]" data-node-id="12:1026" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute bottom-0 left-[73.28%] right-1/4 top-0" data-node-id="12:1027" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_24.22%_0_74.06%]" data-node-id="12:1028" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_23.44%_0_74.84%]" data-node-id="12:1029" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_22.66%_0_75.63%]" data-node-id="12:1030" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_21.88%_0_76.41%]" data-node-id="12:1031" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_21.09%_0_77.19%]" data-node-id="12:1032" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_20.31%_0_77.97%]" data-node-id="12:1033" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_19.53%_0_78.75%]" data-node-id="12:1034" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_18.75%_0_79.53%]" data-node-id="12:1035" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_17.97%_0_80.31%]" data-node-id="12:1036" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_17.19%_0_81.09%]" data-node-id="12:1037" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_16.41%_0_81.88%]" data-node-id="12:1038" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_15.63%_0_82.66%]" data-node-id="12:1039" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_14.84%_0_83.44%]" data-node-id="12:1040" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_14.06%_0_84.22%]" data-node-id="12:1041" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_13.28%_0_85%]" data-node-id="12:1042" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_12.5%_0_85.78%]" data-node-id="12:1043" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_11.72%_0_86.56%]" data-node-id="12:1044" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_10.94%_0_87.34%]" data-node-id="12:1045" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_10.16%_0_88.13%]" data-node-id="12:1046" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_9.38%_0_88.91%]" data-node-id="12:1047" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_8.59%_0_89.69%]" data-node-id="12:1048" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_7.81%_0_90.47%]" data-node-id="12:1049" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_7.03%_0_91.25%]" data-node-id="12:1050" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_6.25%_0_92.03%]" data-node-id="12:1051" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_5.47%_0_92.81%]" data-node-id="12:1052" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_4.69%_0_93.59%]" data-node-id="12:1053" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_3.91%_0_94.38%]" data-node-id="12:1054" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_3.13%_0_95.16%]" data-node-id="12:1055" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_2.34%_0_95.94%]" data-node-id="12:1056" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_1.56%_0_96.72%]" data-node-id="12:1057" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_0.78%_0_97.5%]" data-node-id="12:1058" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_0_0_98.28%]" data-node-id="12:1059" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_-0.78%_0_99.06%]" data-node-id="12:1060" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
        <div className="absolute inset-[0_-1.56%_0_99.84%]" data-node-id="12:1061" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector} />
        </div>
        <div className="absolute inset-[0_-2.34%_0_100.63%]" data-node-id="12:1062" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector1} />
        </div>
        <div className="absolute inset-[0_-3.13%_0_101.41%]" data-node-id="12:1063" data-name="Vector">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgVector2} />
        </div>
      </div>
      <div className="bg-[var(--blue\/600,#3c62b8)] content-stretch flex items-start justify-between overflow-clip px-[48px] py-[40px] relative shrink-0 w-full" data-node-id="12:1064" data-name="Footer">
        <div className="content-stretch flex flex-col gap-[8px] items-start relative shrink-0" data-node-id="12:1065" data-name="Footer left">
          <div className="content-stretch flex gap-[10px] items-center relative shrink-0" data-node-id="12:1066" data-name="Logo">
            <div className="relative shrink-0 size-[32px]" data-node-id="12:1067" data-name="Logo mark">
              <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgLogoMark} />
            </div>
            <p className="[word-break:break-word] font-['Public_Sans:ExtraBold'] font-extrabold leading-[normal] relative shrink-0 text-[22px] text-[color:var(--white,white)] whitespace-nowrap" data-node-id="12:1071">
              DokyuGo
            </p>
          </div>
          <p className="[word-break:break-word] font-['Public_Sans:Regular'] font-normal leading-[normal] relative shrink-0 text-[15px] text-[color:var(--footer-text,#e4ecfb)] whitespace-nowrap" data-node-id="12:1072">
            [BARANGAY NAME] · [HALL ADDRESS]
          </p>
          <p className="[word-break:break-word] font-['Public_Sans:Bold'] font-bold leading-[normal] relative shrink-0 text-[15px] text-[color:var(--white,white)] whitespace-nowrap" data-node-id="12:1073">
            Salamat po!
          </p>
        </div>
        <div className="[word-break:break-word] content-stretch flex font-['Public_Sans:Regular'] font-normal gap-[28px] items-start leading-[normal] relative shrink-0 text-[15px] text-[color:var(--white,white)] whitespace-nowrap" data-node-id="12:1074" data-name="Footer links">
          <p className="relative shrink-0" data-node-id="12:1075">
            Documents
          </p>
          <p className="relative shrink-0" data-node-id="12:1076">
            How it works
          </p>
          <p className="relative shrink-0" data-node-id="12:1077">
            Privacy notice
          </p>
          <p className="relative shrink-0" data-node-id="12:1078">
            Staff login
          </p>
        </div>
        <div className="absolute left-[1110px] size-[200px] top-[-40px]" data-node-id="12:1079" data-name="Sun">
          <img alt="" className="absolute block inset-0 max-w-none size-full" src={imgSun1} />
        </div>
      </div>
    </div>
  );
}
